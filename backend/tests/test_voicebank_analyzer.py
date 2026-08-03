import numpy as np
import soundfile as sf

from app.voicebank.analyzer import _clear_voice_onset_ms, analyze_sample


def test_analyzer_detects_pitch_and_builds_stable_loop(tmp_path):
    sample_rate = 44100
    silence = np.zeros(round(0.3 * sample_rate), dtype=np.float32)
    time = np.arange(round(1.8 * sample_rate), dtype=np.float32) / sample_rate
    voice = 0.35 * np.sin(2 * np.pi * 220.0 * time)
    audio = np.concatenate([silence, voice, silence])
    source = tmp_path / "a.wav"
    sf.write(source, audio, sample_rate, subtype="PCM_24")

    processed, analysis = analyze_sample(source, "a")

    assert processed.size < audio.size
    assert analysis.base_pitch == "A3"
    assert abs(analysis.detected_frequency_hz - 220.0) < 1.0
    assert analysis.voiced_start_ms <= 10
    assert analysis.attack_ms == 40
    assert analysis.loop_end_ms - analysis.loop_start_ms >= 400
    assert not analysis.clipped


def test_analyzer_ignores_octave_outliers(tmp_path):
    sample_rate = 44100
    first_time = np.arange(round(0.45 * sample_rate), dtype=np.float32) / sample_rate
    stable_time = np.arange(round(1.5 * sample_rate), dtype=np.float32) / sample_rate
    octave_error = 0.2 * np.sin(2 * np.pi * 110.0 * first_time)
    stable_voice = 0.35 * np.sin(2 * np.pi * 220.0 * stable_time)
    source = tmp_path / "a.wav"
    sf.write(source, np.concatenate([octave_error, stable_voice]), sample_rate)

    _, analysis = analyze_sample(source, "a")

    assert analysis.base_pitch == "A3"
    assert analysis.pitch_std_cents < 10


def test_analyzer_preserves_a_longer_consonant_attack(tmp_path):
    sample_rate = 44100
    noise = np.random.default_rng(7).normal(0, 0.04, round(0.18 * sample_rate))
    time = np.arange(round(1.5 * sample_rate), dtype=np.float32) / sample_rate
    voice = 0.35 * np.sin(2 * np.pi * 220.0 * time)
    source = tmp_path / "shi.wav"
    sf.write(source, np.concatenate([noise, voice]), sample_rate)

    processed, analysis = analyze_sample(source, "shi")

    assert analysis.attack_ms >= _clear_voice_onset_ms(processed, sample_rate) + 60


def test_analyzer_removes_a_long_low_level_preamble(tmp_path):
    sample_rate = 44100
    quiet_time = np.arange(round(0.8 * sample_rate), dtype=np.float32) / sample_rate
    voice_time = np.arange(round(1.5 * sample_rate), dtype=np.float32) / sample_rate
    quiet_preamble = 0.01 * np.sin(2 * np.pi * 208.0 * quiet_time)
    voice = 0.35 * np.sin(2 * np.pi * 208.0 * voice_time)
    source = tmp_path / "yu.wav"
    sf.write(source, np.concatenate([quiet_preamble, voice]), sample_rate)

    processed, analysis = analyze_sample(source, "yu")

    assert processed.size / sample_rate < 1.8
    assert analysis.attack_ms >= 120


def test_analyzer_prefers_loop_points_with_matching_endpoint_levels(tmp_path):
    sample_rate = 44100
    time = np.arange(round(2.4 * sample_rate), dtype=np.float32) / sample_rate
    envelope = 0.24 + 0.08 * np.sin(2 * np.pi * 0.8 * time)
    voice = envelope * np.sin(2 * np.pi * 220.0 * time)
    source = tmp_path / "yu.wav"
    sf.write(source, voice, sample_rate)

    processed, analysis = analyze_sample(source, "yu")
    start = round(analysis.loop_start_ms * sample_rate / 1000)
    end = round(analysis.loop_end_ms * sample_rate / 1000)
    edge = round(0.06 * sample_rate)
    start_rms = np.sqrt(np.mean(np.square(processed[start : start + edge])))
    end_rms = np.sqrt(np.mean(np.square(processed[end - edge : end])))
    endpoint_delta_db = abs(20 * np.log10(end_rms / start_rms))
    overlap = round(0.02 * sample_rate)
    waveform_correlation = np.corrcoef(
        processed[start : start + overlap], processed[end - overlap : end]
    )[0, 1]

    assert endpoint_delta_db < 1.0
    assert waveform_correlation > 0.5
