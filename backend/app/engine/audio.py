from typing import Optional

import librosa
import numpy as np
import soundfile as sf

from app.core.errors import MiniSvsError
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
    phoneme = note.lyric.strip().lower()
    sample_metadata = voicebank.metadata.phonemes.get(phoneme)
    if sample_metadata is None:
        raise MiniSvsError(
            "unsupported_phoneme",
            f"Voicebank '{voicebank.metadata.id}' does not contain phoneme '{phoneme}'.",
            details={"voicebankId": voicebank.metadata.id, "phoneme": phoneme},
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

    if target_frames <= loop_start + release_frames:
        output = np.array(sample[:target_frames], copy=True)
        fade = min(release_frames, output.size)
        if fade:
            output[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
        return _pad_to_length(output, target_frames)

    attack = sample[:loop_start]
    sustain = sample[loop_start:loop_end]
    release = sample[-min(release_frames, sample.size) :]
    crossfade = min(round(sample_rate * 0.02), sustain.size // 4)
    release_crossfade = min(crossfade, release.size, sustain.size // 2)
    sustain_frames = target_frames - attack.size - release.size + release_crossfade
    looped = _loop_region(sustain, max(1, sustain_frames), crossfade)
    output = _append_crossfade(np.concatenate([attack, looped]), release, release_crossfade)
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
    shifted = librosa.effects.pitch_shift(audio, sr=sample_rate, n_steps=steps)
    return _pad_to_length(np.asarray(shifted, dtype=np.float32), audio.size)
