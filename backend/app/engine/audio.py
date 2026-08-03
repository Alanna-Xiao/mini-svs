import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import librosa
import numpy as np
import pyrubberband as pyrb
import soundfile as sf

from app.core.errors import MiniSvsError
from app.lyrics import lyric_to_phonemes
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
    pitch_glide_frames: int = 0,
) -> np.ndarray:
    entered_lyric = note.lyric.strip()
    direct_phoneme = entered_lyric.lower()
    if direct_phoneme in voicebank.metadata.phonemes:
        phonemes = (direct_phoneme,)
    else:
        phonemes = lyric_to_phonemes(entered_lyric)
    missing_phonemes = tuple(
        phoneme for phoneme in phonemes if phoneme not in voicebank.metadata.phonemes
    )
    if not phonemes or missing_phonemes:
        resolved = ", ".join(phonemes) or "(empty)"
        missing = ", ".join(missing_phonemes) or resolved
        details = {
            "voicebankId": voicebank.metadata.id,
            "lyric": entered_lyric,
            "phoneme": missing_phonemes[0] if len(missing_phonemes) == 1 else resolved,
        }
        if len(phonemes) > 1:
            details.update(
                {
                    "phonemes": list(phonemes),
                    "missingPhonemes": list(missing_phonemes),
                }
            )
        raise MiniSvsError(
            "unsupported_phoneme",
            (
                f"Lyric '{entered_lyric}' resolves to phonemes '{resolved}', but voicebank "
                f"'{voicebank.metadata.id}' does not contain: {missing}."
            ),
            details=details,
        )

    total_frames = max(1, duration_frames + transition_frames)
    internal_crossfade = min(
        round(sample_rate * 0.015),
        total_frames // max(1, len(phonemes) * 4),
    )
    render_budget = total_frames + internal_crossfade * (len(phonemes) - 1)
    segment_frames = _divide_frames(render_budget, len(phonemes))
    rendered_segments = []
    for index, (phoneme, frames) in enumerate(zip(phonemes, segment_frames)):
        rendered_segments.append(
            _render_phoneme(
                phoneme,
                note,
                voicebank,
                frames,
                sample_rate,
                transition_frames=(
                    transition_frames if index == len(phonemes) - 1 else 0
                ),
                next_pitch=(next_pitch if index == len(phonemes) - 1 else None),
                fade_in_frames=(fade_in_frames if index == 0 else 0),
                pitch_glide_frames=(
                    pitch_glide_frames if index == len(phonemes) - 1 else 0
                ),
                fade_start=index == 0,
                fade_end=index == len(phonemes) - 1,
            )
        )

    rendered = rendered_segments[0]
    for segment in rendered_segments[1:]:
        rendered = _append_crossfade(rendered, segment, internal_crossfade)
    rendered = _pad_to_length(rendered, total_frames)

    peak = float(np.max(np.abs(rendered)))
    if peak > 0:
        rendered *= min(4.0, 0.65 / peak)
    return np.asarray(rendered, dtype=np.float32)


def _render_phoneme(
    phoneme: str,
    note: VocalNote,
    voicebank: LoadedVoicebank,
    target_frames: int,
    sample_rate: int,
    transition_frames: int = 0,
    next_pitch: Optional[str] = None,
    fade_in_frames: int = 0,
    pitch_glide_frames: int = 0,
    fade_start: bool = True,
    fade_end: bool = True,
) -> np.ndarray:
    sample_metadata = voicebank.metadata.phonemes[phoneme]
    sample = _load_sample(voicebank.sample_path(phoneme), sample_rate)
    sustained = _match_duration(
        sample,
        sample_metadata,
        max(1, target_frames),
        sample_rate,
        include_release=fade_end and transition_frames == 0,
    )
    current_steps = pitch_to_midi(note.pitch) - pitch_to_midi(sample_metadata.base_pitch)

    if transition_frames and next_pitch is not None:
        next_steps = pitch_to_midi(next_pitch) - pitch_to_midi(sample_metadata.base_pitch)
        boundary = max(0, sustained.size - transition_frames)
        glide_frames = min(max(1, pitch_glide_frames), sustained.size)
        glide_start = max(0, boundary - glide_frames // 2)
        glide_end = min(sustained.size, glide_start + glide_frames)
        rendered = _pitch_shift_with_glide(
            sustained,
            sample_rate,
            current_steps,
            next_steps,
            glide_start,
            glide_end,
        )
        fade_frames = rendered.size - boundary
        fade_phase = np.linspace(0.0, np.pi / 2, fade_frames, dtype=np.float32)
        rendered[boundary:] *= np.cos(fade_phase)
    else:
        rendered = _pitch_shift(sustained, sample_rate, current_steps)

    if fade_in_frames:
        count = min(fade_in_frames, rendered.size)
        phase = np.linspace(0.0, np.pi / 2, count, dtype=np.float32)
        rendered[:count] *= np.sin(phase)

    edge_frames = min(max(1, round(sample_rate * 0.005)), rendered.size // 2)
    if edge_frames:
        if fade_start and not fade_in_frames:
            rendered[:edge_frames] *= np.linspace(0.0, 1.0, edge_frames, dtype=np.float32)
        if fade_end and transition_frames == 0:
            rendered[-edge_frames:] *= np.linspace(1.0, 0.0, edge_frames, dtype=np.float32)
    return np.asarray(rendered, dtype=np.float32)


def _divide_frames(total_frames: int, parts: int) -> list[int]:
    base, remainder = divmod(total_frames, parts)
    return [base + (1 if index < remainder else 0) for index in range(parts)]


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
    include_release: bool = True,
) -> np.ndarray:
    loop_start = round(metadata.loop_start_ms * sample_rate / 1000)
    loop_end = round(metadata.loop_end_ms * sample_rate / 1000)
    release_frames = (
        round(metadata.release_ms * sample_rate / 1000) if include_release else 0
    )
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
    release = sample[-release_frames:] if release_frames else np.zeros(0, dtype=np.float32)
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
    if release.size:
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


def _pitch_shift_with_glide(
    audio: np.ndarray,
    sample_rate: int,
    current_steps: float,
    next_steps: float,
    glide_start: int,
    glide_end: int,
) -> np.ndarray:
    if current_steps == next_steps:
        return _pitch_shift(audio, sample_rate, current_steps)
    if shutil.which("rubberband") is None:
        raise MiniSvsError(
            "pitch_engine_unavailable",
            "Rubber Band is required for formant-preserving vocal pitch shifts.",
        )

    with tempfile.TemporaryDirectory(prefix="mini-svs-glide-") as directory:
        root = Path(directory)
        input_path = root / "input.wav"
        output_path = root / "output.wav"
        pitchmap_path = root / "pitchmap.txt"
        sf.write(input_path, audio, sample_rate, subtype="FLOAT")
        points = {
            0: current_steps,
            max(0, glide_start): current_steps,
            min(audio.size - 1, glide_end): next_steps,
            audio.size - 1: next_steps,
        }
        pitchmap_path.write_text(
            "".join(f"{frame} {steps:.8f}\n" for frame, steps in sorted(points.items())),
            encoding="ascii",
        )
        try:
            result = subprocess.run(
                [
                    "rubberband",
                    "--quiet",
                    "--fine",
                    "--formant",
                    "--pitchmap",
                    str(pitchmap_path),
                    str(input_path),
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except subprocess.TimeoutExpired as error:
            raise MiniSvsError(
                "pitch_shift_failed", "Rubber Band timed out while applying a pitch glide."
            ) from error
        if result.returncode != 0 or not output_path.is_file():
            raise MiniSvsError(
                "pitch_shift_failed",
                "Rubber Band could not apply the vocal pitch glide.",
                details={"reason": result.stderr.strip()},
            )
        shifted, rendered_rate = sf.read(output_path, dtype="float32", always_2d=False)
        if rendered_rate != sample_rate:
            raise MiniSvsError(
                "pitch_shift_failed",
                "Rubber Band returned a pitch glide at an unexpected sample rate.",
            )
        if shifted.ndim == 2:
            shifted = np.mean(shifted, axis=1)
    return _pad_to_length(np.asarray(shifted, dtype=np.float32), audio.size)
