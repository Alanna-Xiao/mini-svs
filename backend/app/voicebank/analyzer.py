from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple

import librosa
import numpy as np
import soundfile as sf


@dataclass(frozen=True)
class SampleAnalysis:
    phoneme: str
    original_duration_seconds: float
    processed_duration_seconds: float
    detected_frequency_hz: float
    detected_midi: float
    base_pitch: str
    pitch_std_cents: float
    peak_amplitude: float
    clipped: bool
    snr_db: float
    voiced_start_ms: int
    voiced_end_ms: int
    loop_start_ms: int
    loop_end_ms: int
    attack_ms: int
    release_ms: int
    warnings: List[str]

    def report(self) -> dict:
        return asdict(self)


def analyze_sample(
    source: Path,
    phoneme: str,
    sample_rate: int = 44100,
) -> Tuple[np.ndarray, SampleAnalysis]:
    audio, source_rate = sf.read(source, dtype="float32", always_2d=False)
    if audio.ndim == 2:
        audio = np.mean(audio, axis=1)
    if source_rate != sample_rate:
        audio = librosa.resample(audio, orig_sr=source_rate, target_sr=sample_rate)
    if audio.size == 0:
        raise ValueError(f"Sample '{source}' is empty.")

    original_duration = audio.size / sample_rate
    intervals = librosa.effects.split(audio, top_db=35)
    if len(intervals) == 0:
        raise ValueError(f"Sample '{source}' does not contain detectable voice audio.")
    active_start, active_end = max(intervals, key=lambda interval: interval[1] - interval[0])

    padding_before = int(0.005 * sample_rate)
    padding_after = int(0.12 * sample_rate)
    trim_start = max(0, int(active_start) - padding_before)
    trim_end = min(audio.size, int(active_end) + padding_after)
    processed = np.asarray(audio[trim_start:trim_end], dtype=np.float32)
    voiced_start_seconds = (active_start - trim_start) / sample_rate
    voiced_end_seconds = (active_end - trim_start) / sample_rate

    hop_length = 256
    frame_length = 2048
    f0, voiced_flag, _ = librosa.pyin(
        processed,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sample_rate,
        frame_length=frame_length,
        hop_length=hop_length,
    )
    times = librosa.times_like(f0, sr=sample_rate, hop_length=hop_length)
    valid = voiced_flag & np.isfinite(f0)
    valid &= times >= voiced_start_seconds
    valid &= times <= voiced_end_seconds
    if np.count_nonzero(valid) < 8:
        raise ValueError(f"Could not detect a stable pitch in sample '{source}'.")

    raw_midi = librosa.hz_to_midi(f0[valid])
    dominant_center = max(
        raw_midi,
        key=lambda center: np.count_nonzero(np.abs(raw_midi - center) <= 1.5),
    )
    full_midi = librosa.hz_to_midi(f0)
    valid &= np.abs(full_midi - dominant_center) <= 1.5
    midi_values = full_midi[valid]
    if midi_values.size < 8:
        raise ValueError(f"Could not isolate a stable pitch cluster in sample '{source}'.")
    detected_midi = float(np.median(midi_values))
    detected_frequency = float(librosa.midi_to_hz(detected_midi))
    base_pitch = str(librosa.midi_to_note(round(detected_midi), unicode=False))
    pitch_std_cents = float(np.std((midi_values - detected_midi) * 100.0))

    loop_start, loop_end = _find_stable_loop(
        processed,
        f0,
        valid,
        times,
        detected_midi,
        voiced_start_seconds,
        voiced_end_seconds,
        sample_rate,
        hop_length,
    )

    peak = float(np.max(np.abs(processed)))
    noise = np.concatenate(
        [
            processed[: max(1, int(voiced_start_seconds * sample_rate))],
            processed[min(processed.size, int(voiced_end_seconds * sample_rate)) :],
        ]
    )
    voice_rms = float(np.sqrt(np.mean(np.square(processed[active_start - trim_start : active_end - trim_start]))))
    noise_rms = float(np.sqrt(np.mean(np.square(noise)))) if noise.size else 1e-9
    snr_db = float(20.0 * np.log10(max(voice_rms, 1e-9) / max(noise_rms, 1e-9)))

    warnings = []
    if peak >= 0.99:
        warnings.append("possible_clipping")
    if pitch_std_cents > 35:
        warnings.append("unstable_pitch")
    if snr_db < 20:
        warnings.append("high_background_noise")

    fade_frames = min(int(0.005 * sample_rate), processed.size // 2)
    if fade_frames:
        processed[:fade_frames] *= np.linspace(0.0, 1.0, fade_frames, dtype=np.float32)
        processed[-fade_frames:] *= np.linspace(1.0, 0.0, fade_frames, dtype=np.float32)

    analysis = SampleAnalysis(
        phoneme=phoneme,
        original_duration_seconds=round(original_duration, 4),
        processed_duration_seconds=round(processed.size / sample_rate, 4),
        detected_frequency_hz=round(detected_frequency, 2),
        detected_midi=round(detected_midi, 3),
        base_pitch=base_pitch,
        pitch_std_cents=round(pitch_std_cents, 2),
        peak_amplitude=round(peak, 4),
        clipped=peak >= 0.99,
        snr_db=round(snr_db, 2),
        voiced_start_ms=round(voiced_start_seconds * 1000),
        voiced_end_ms=round(voiced_end_seconds * 1000),
        loop_start_ms=round(loop_start * 1000),
        loop_end_ms=round(loop_end * 1000),
        attack_ms=min(80, max(20, round(voiced_start_seconds * 1000 + 30))),
        release_ms=120,
        warnings=warnings,
    )
    return processed, analysis


def _find_stable_loop(
    audio: np.ndarray,
    f0: np.ndarray,
    valid: np.ndarray,
    times: np.ndarray,
    detected_midi: float,
    voiced_start: float,
    voiced_end: float,
    sample_rate: int,
    hop_length: int,
) -> Tuple[float, float]:
    rms = librosa.feature.rms(
        y=audio, frame_length=2048, hop_length=hop_length, center=True
    )[0]
    frame_count = min(len(f0), len(rms))
    window_frames = max(8, round(0.5 * sample_rate / hop_length))
    margin = min(0.35, max(0.15, (voiced_end - voiced_start) * 0.18))
    candidate_start = voiced_start + margin
    candidate_end = voiced_end - margin
    best = None

    for start in range(0, frame_count - window_frames + 1):
        end = start + window_frames
        if times[start] < candidate_start or times[end - 1] > candidate_end:
            continue
        window_valid = valid[start:end]
        if np.count_nonzero(window_valid) < window_frames * 0.8:
            continue
        cents = (librosa.hz_to_midi(f0[start:end][window_valid]) - detected_midi) * 100
        rms_window = np.maximum(rms[start:end][window_valid], 1e-9)
        rms_db = librosa.amplitude_to_db(rms_window, ref=np.max)
        score = float(np.std(cents) + 0.7 * np.std(rms_db))
        if best is None or score < best[0]:
            best = (score, start, end)

    if best is None:
        fallback_start = max(voiced_start + 0.15, (voiced_start + voiced_end) / 2 - 0.25)
        fallback_end = min(voiced_end - 0.15, fallback_start + 0.5)
        if fallback_end - fallback_start < 0.25:
            raise ValueError("The stable voiced region is too short to create a loop.")
        return fallback_start, fallback_end
    return float(times[best[1]]), float(times[best[2] - 1])
