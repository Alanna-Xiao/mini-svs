import numpy as np
import pytest
import soundfile as sf

from app.core.errors import MiniSvsError
from app.engine.audio import _match_duration
from app.engine.sample import SampleEngine, ticks_to_seconds
from app.schemas.project import VocalNote, VocalTrack
from app.voicebank.models import LoadedVoicebank, PhonemeMetadata, VoicebankMetadata


def make_voicebank(tmp_path, phonemes=("a",)) -> LoadedVoicebank:
    root = tmp_path / "test_voice"
    samples = root / "samples"
    samples.mkdir(parents=True)
    sample_rate = 44100
    time = np.arange(sample_rate, dtype=np.float32) / sample_rate
    audio = 0.4 * np.sin(2 * np.pi * 220 * time)
    entries = {}
    for phoneme in phonemes:
        sf.write(samples / f"{phoneme}.wav", audio, sample_rate, subtype="PCM_16")
        entries[phoneme] = {
            "sample": f"samples/{phoneme}.wav",
            "basePitch": "A3",
            "attackMs": 50,
            "loopStartMs": 100,
            "loopEndMs": 700,
            "releaseMs": 100,
        }
    metadata = VoicebankMetadata.model_validate(
        {
            "id": "test_voice",
            "name": "Test Voice",
            "language": "test",
            "type": "sample",
            "license": {"code": "test", "summary": "Test only"},
            "phonemes": entries,
        }
    )
    return LoadedVoicebank(root=root, metadata=metadata)


def vocal_track(notes):
    return VocalTrack(
        id="vocal_1",
        type="vocal",
        name="Vocal",
        voicebankId="test_voice",
        notes=notes,
    )


def test_grid_ticks_convert_to_seconds():
    assert ticks_to_seconds(4, 120, "1/16") == pytest.approx(0.5)


def test_engine_renders_note_at_requested_duration_and_pitch(tmp_path):
    note = VocalNote(id="note_1", type="vocal", pitch="A4", start=0, duration=4, lyric="a")
    audio = SampleEngine().render_track(
        vocal_track([note]), make_voicebank(tmp_path), 120, "1/16", 44100
    )

    assert audio.size == 22050
    assert 0.4 < np.max(np.abs(audio)) <= 0.66
    crossings = np.flatnonzero(np.diff(np.signbit(audio[4410:17640])))
    frequency = crossings.size / (2 * (13230 / 44100))
    assert frequency == pytest.approx(440, rel=0.05)


def test_engine_blends_adjacent_notes_without_changing_project_length(tmp_path):
    notes = [
        VocalNote(id="note_1", type="vocal", pitch="A3", start=0, duration=4, lyric="a"),
        VocalNote(id="note_2", type="vocal", pitch="C4", start=4, duration=4, lyric="a"),
    ]
    audio = SampleEngine().render_track(
        vocal_track(notes), make_voicebank(tmp_path), 120, "1/16", 44100
    )

    assert audio.size == 44100
    assert np.isfinite(audio).all()


def test_engine_rejects_phonemes_missing_from_voicebank(tmp_path):
    note = VocalNote(id="note_1", type="vocal", pitch="A3", start=0, duration=4, lyric="i")
    with pytest.raises(MiniSvsError) as error:
        SampleEngine().render_track(
            vocal_track([note]), make_voicebank(tmp_path), 120, "1/16", 44100
        )
    assert error.value.code == "unsupported_phoneme"
    assert error.value.details == {
        "voicebankId": "test_voice",
        "lyric": "i",
        "phoneme": "i",
    }


@pytest.mark.parametrize("lyric", ["あ", "ア"])
def test_engine_resolves_kana_lyrics_to_voicebank_phonemes(tmp_path, lyric):
    note = VocalNote(id="note_1", type="vocal", pitch="A3", start=0, duration=4, lyric=lyric)

    audio = SampleEngine().render_track(
        vocal_track([note]), make_voicebank(tmp_path), 120, "1/16", 44100
    )

    assert audio.size == 22050
    assert np.max(np.abs(audio)) > 0


def test_engine_resolves_kanji_lyrics_to_voicebank_phonemes(tmp_path):
    note = VocalNote(id="note_1", type="vocal", pitch="A3", start=0, duration=4, lyric="絵")

    audio = SampleEngine().render_track(
        vocal_track([note]), make_voicebank(tmp_path, phonemes=("e",)), 120, "1/16", 44100
    )

    assert audio.size == 22050
    assert np.max(np.abs(audio)) > 0


def test_engine_renders_multiple_kana_inside_one_note(tmp_path):
    note = VocalNote(id="note_1", type="vocal", pitch="A3", start=0, duration=8, lyric="かな")

    audio = SampleEngine().render_track(
        vocal_track([note]),
        make_voicebank(tmp_path, phonemes=("ka", "na")),
        120,
        "1/16",
        44100,
    )

    assert audio.size == 44100
    assert np.max(np.abs(audio)) > 0


def test_engine_reports_missing_phonemes_from_a_multi_kana_lyric(tmp_path):
    note = VocalNote(id="note_1", type="vocal", pitch="A3", start=0, duration=8, lyric="かな")

    with pytest.raises(MiniSvsError) as error:
        SampleEngine().render_track(
            vocal_track([note]),
            make_voicebank(tmp_path, phonemes=("ka",)),
            120,
            "1/16",
            44100,
        )

    assert error.value.details["phonemes"] == ["ka", "na"]
    assert error.value.details["missingPhonemes"] == ["na"]


def test_engine_prefers_a_voicebank_native_kana_key(tmp_path):
    note = VocalNote(id="note_1", type="vocal", pitch="A3", start=0, duration=4, lyric="あ")

    audio = SampleEngine().render_track(
        vocal_track([note]), make_voicebank(tmp_path, phonemes=("あ",)), 120, "1/16", 44100
    )

    assert audio.size == 22050
    assert np.max(np.abs(audio)) > 0


def test_engine_reports_resolved_phoneme_when_voicebank_sample_is_missing(tmp_path):
    note = VocalNote(id="note_1", type="vocal", pitch="A3", start=0, duration=4, lyric="か")

    with pytest.raises(MiniSvsError) as error:
        SampleEngine().render_track(
            vocal_track([note]), make_voicebank(tmp_path), 120, "1/16", 44100
        )

    assert error.value.code == "unsupported_phoneme"
    assert error.value.details["lyric"] == "か"
    assert error.value.details["phoneme"] == "ka"


def test_engine_limits_gain_for_quiet_recordings(tmp_path):
    voicebank = make_voicebank(tmp_path)
    sample_path = voicebank.sample_path("a")
    sample, sample_rate = sf.read(sample_path, dtype="float32")
    sf.write(sample_path, sample * 0.01, sample_rate, subtype="PCM_16")
    note = VocalNote(id="note_1", type="vocal", pitch="A3", start=0, duration=4, lyric="a")

    audio = SampleEngine().render_track(
        vocal_track([note]), voicebank, 120, "1/16", sample_rate
    )

    assert np.max(np.abs(audio)) < 0.02


def test_duration_matching_preserves_the_configured_consonant_attack():
    sample_rate = 1000
    attack = np.linspace(-0.2, 0.2, 200, dtype=np.float32)
    gap = np.full(200, 0.3, dtype=np.float32)
    sustain = np.full(400, 0.6, dtype=np.float32)
    release = np.linspace(0.2, 0.0, 200, dtype=np.float32)
    sample = np.concatenate([attack, gap, sustain, release])
    metadata = PhonemeMetadata.model_validate(
        {
            "sample": "samples/ka.wav",
            "basePitch": "A3",
            "attackMs": 180,
            "loopStartMs": 400,
            "loopEndMs": 800,
            "releaseMs": 100,
        }
    )

    rendered = _match_duration(sample, metadata, 500, sample_rate)

    assert rendered.size == 500
    assert rendered[150] == pytest.approx(attack[150])
