import shutil
from typing import Optional

import librosa
import numpy as np
import pyrubberband as pyrb
import soundfile as sf

from app.core.errors import MiniSvsError
from app.lyrics import lyric_to_phoneme
from app.schemas.project import VocalNote, pitch_to_midi
from app.voicebank.models import LoadedVoicebank, PhonemeMetadata


def render_vocal_note(
    note: VocalNote,
    voicebank: LoadedVoicebank,
    duration_frames: int,
    sample_rate: int,
    transition_frames: int = 0,
    next_pitch: Optional[str] = None,
    fade_in_frames: int = 0,
) -> np.ndarray:
    entered_lyric = note.lyric.strip()
    phoneme = entered_lyric.lower()
    sample_metadata = voicebank.metadata.phonemes.get(phoneme)
    if sample_metadata is None:
        phoneme = lyric_to_phoneme(entered_lyric)
        sample_metadata = voicebank.metadata.phonemes.get(phoneme)
    if sample_metadata is None:
        raise MiniSvsError(
            "unsupported_phoneme",
            (
                f"Lyric '{entered_lyric}' resolves to phoneme '{phoneme}', but voicebank "
                f"'{voicebank.metadata.id}' does not contain that phoneme."
            ),
            details={
                "voicebankId": voicebank.metadata.id,
                "lyric": entered_lyric,
                "phoneme": phoneme,
            },
        )

    sample = _load_sample(voicebank.sample_path(phoneme), sample_rate)
    total_frames = max(1, duration_frames + transition_frames)
    sustained = _match_duration(sample, sample_metadata, total_frames, sample_rate)
    current_steps = pitch_to_midi(note.pitch) - pitch_to_midi(sample_metadata.base_pitch)
    rendered = _pitch_shift(sustained, sample_rate, current_steps)

    if transition_frames and next_pitch is not None:
        next_steps = pitch_to_midi(next_pitch) - pitch_to_midi(sample_metadata.base_pitch)
        target = _pitch_shift(sustained, sample_rate, next_steps)
        start = max(0, rendered.size - transition_frames)
        blend_frames = rendered.size - start
        blend = np.linspace(0.0, 1.0, blend_frames, dtype=np.float32)
        rendered[start:] = rendered[start:] * (1.0 - blend) + target[start:] * blend
        rendered[start:] *= np.linspace(1.0, 0.0, blend_frames, dtype=np.float32)

    if fade_in_frames:
        count = min(fade_in_frames, rendered.size)
        rendered[:count] *= np.linspace(0.0, 1.0, count, dtype=np.float32)

    edge_frames = min(max(1, round(sample_rate * 0.005)), rendered.size // 2)
    if edge_frames:
        rendered[:edge_frames] *= np.linspace(0.0, 1.0, edge_frames, dtype=np.float32)
        if transition_frames == 0:
            rendered[-edge_frames:] *= np.linspace(1.0, 0.0, edge_frames, dtype=np.float32)

    peak = float(np.max(np.abs(rendered)))
    if peak > 0:
        rendered *= min(4.0, 0.65 / peak)
    return np.asarray(rendered, dtype=np.float32)


def _load_sample(path, sample_rate: int) -> np.ndarray:
    try:
        sample, source_rate = sf.read(path, dtype="float32", always_2d=False)
    except (OSError, RuntimeError) as error:
        raise MiniSvsError(
            "invalid_voicebank_sample",
            f"Could not read voicebank sample '{path.name}'.",
            details={"reason": str(error)},
        ) from error
    if sample.ndim == 2:
        sample = np.mean(sample, axis=1)
    if sample.size == 0:
        raise MiniSvsError(
            "invalid_voicebank_sample",
            f"Voicebank sample '{path.name}' is empty.",
        )
    if source_rate != sample_rate:
        sample = librosa.resample(sample, orig_sr=source_rate, target_sr=sample_rate)
    return np.asarray(sample, dtype=np.float32)


def _match_duration(
    sample: np.ndarray,
    metadata: PhonemeMetadata,
    target_frames: int,
    sample_rate: int,
) -> np.ndarray:
    loop_start = round(metadata.loop_start_ms * sample_rate / 1000)
    loop_end = round(metadata.loop_end_ms * sample_rate / 1000)
    release_frames = round(metadata.release_ms * sample_rate / 1000)
    if not 0 <= loop_start < loop_end <= sample.size:
        raise MiniSvsError(
            "invalid_loop_points",
            "Voicebank loop points are outside the sample.",
            details={"loopStartMs": metadata.loop_start_ms, "loopEndMs": metadata.loop_end_ms},
        )

    release_frames = min(release_frames, max(1, target_frames // 4))
    minimum_sustain_frames = min(
        round(sample_rate * 0.08), max(1, target_frames // 5)
    )
    attack_frames = min(
        loop_start,
        round(metadata.attack_ms * sample_rate / 1000),
        max(1, target_frames - release_frames - minimum_sustain_frames),
    )
    attack = sample[:attack_frames]
    sustain = sample[loop_start:loop_end]
    release = sample[-release_frames:]
    loop_crossfade = min(round(sample_rate * 0.02), sustain.size // 4)
    attack_crossfade = min(round(sample_rate * 0.01), attack.size, sustain.size // 2)
    release_crossfade = min(loop_crossfade, release.size, sustain.size // 2)
    sustain_frames = max(
        1,
        target_frames
        - attack.size
        - release.size
        + attack_crossfade
        + release_crossfade,
    )
    looped = _loop_region(sustain, sustain_frames, loop_crossfade)
    output = _append_crossfade(attack, looped, attack_crossfade)
    output = _append_crossfade(output, release, release_crossfade)
    return _pad_to_length(output, target_frames)


def _loop_region(region: np.ndarray, target_frames: int, crossfade: int) -> np.ndarray:
    if region.size == 0:
        raise MiniSvsError("invalid_loop_points", "The configured sustain loop is empty.")
    output = np.array(region, copy=True)
    while output.size < target_frames:
        output = _append_crossfade(output, region, crossfade)
    return np.asarray(output[:target_frames], dtype=np.float32)


def _append_crossfade(left: np.ndarray, right: np.ndarray, frames: int) -> np.ndarray:
    frames = min(frames, left.size, right.size)
    if frames <= 0:
        return np.concatenate([left, right])
    blend = np.linspace(0.0, 1.0, frames, dtype=np.float32)
    overlap = left[-frames:] * (1.0 - blend) + right[:frames] * blend
    return np.concatenate([left[:-frames], overlap, right[frames:]])


def _pad_to_length(audio: np.ndarray, frames: int) -> np.ndarray:
    if audio.size >= frames:
        return np.asarray(audio[:frames], dtype=np.float32)
    return np.pad(audio, (0, frames - audio.size)).astype(np.float32)


def _pitch_shift(audio: np.ndarray, sample_rate: int, steps: float) -> np.ndarray:
    if steps == 0:
        return np.array(audio, copy=True)
    if shutil.which("rubberband") is None:
        raise MiniSvsError(
            "pitch_engine_unavailable",
            "Rubber Band is required for formant-preserving vocal pitch shifts.",
        )
    try:
        shifted = pyrb.pitch_shift(
            audio,
            sample_rate,
            steps,
            rbargs={"--fine": "", "--formant": ""},
        )
    except (OSError, RuntimeError) as error:
        raise MiniSvsError(
            "pitch_shift_failed",
            "Rubber Band could not pitch-shift the vocal sample.",
            details={"reason": str(error)},
        ) from error
    return _pad_to_length(np.asarray(shifted, dtype=np.float32), audio.size)
