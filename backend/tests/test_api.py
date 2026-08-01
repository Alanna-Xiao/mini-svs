import pytest
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app

client = TestClient(create_app())


@pytest.fixture(autouse=True)
def isolated_asset_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("MINI_SVS_VOICEBANK_DIR", str(tmp_path / "voicebanks"))
    monkeypatch.setenv(
        "MINI_SVS_INSTRUMENT_CONFIG", str(tmp_path / "instruments.json")
    )
    monkeypatch.setenv("MINI_SVS_OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_empty_catalogs():
    assert client.get("/voicebanks").json() == []
    assert client.get("/instruments").json() == []


def test_unknown_voicebank_is_structured_error():
    response = client.post(
        "/render",
        json={
            "projectId": "demo",
            "bpm": 120,
            "grid": "1/16",
            "tracks": [
                {
                    "id": "vocal_1",
                    "type": "vocal",
                    "name": "Main Vocal",
                    "voicebankId": "missing",
                    "notes": [],
                }
            ],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_voicebank"


def test_output_ids_cannot_escape_output_directory():
    response = client.get("/outputs/..%2Fsecret")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_output_id"


def test_request_validation_errors_are_structured():
    response = client.post(
        "/render",
        json={
            "projectId": "demo",
            "bpm": 120,
            "grid": "1/16",
            "tracks": [
                {
                    "id": "vocal_1",
                    "type": "vocal",
                    "name": "Main Vocal",
                    "voicebankId": "author_demo",
                    "notes": [
                        {
                            "id": "note_1",
                            "type": "vocal",
                            "pitch": "invalid",
                            "start": 0,
                            "duration": 4,
                            "lyric": "a",
                        }
                    ],
                }
            ],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_render_writes_downloadable_wav(isolated_asset_paths):
    root = isolated_asset_paths / "voicebanks" / "author_demo"
    samples = root / "samples"
    samples.mkdir(parents=True)
    sample_rate = 44100
    time = np.arange(sample_rate, dtype=np.float32) / sample_rate
    sf.write(samples / "a.wav", 0.4 * np.sin(2 * np.pi * 220 * time), sample_rate)
    (root / "voicebank.json").write_text(
        """{
          "id": "author_demo",
          "name": "Author Demo",
          "language": "test",
          "type": "sample",
          "license": {"code": "custom", "summary": "Test only"},
          "phonemes": {
            "a": {
              "sample": "samples/a.wav",
              "basePitch": "A3",
              "attackMs": 50,
              "loopStartMs": 100,
              "loopEndMs": 700,
              "releaseMs": 100
            }
          }
        }""",
        encoding="utf-8",
    )
    response = client.post(
        "/render",
        json={
            "projectId": "demo",
            "bpm": 120,
            "grid": "1/16",
            "tracks": [
                {
                    "id": "vocal_1",
                    "type": "vocal",
                    "name": "Main Vocal",
                    "voicebankId": "author_demo",
                    "notes": [
                        {
                            "id": "note_1",
                            "type": "vocal",
                            "pitch": "A3",
                            "start": 0,
                            "duration": 4,
                            "lyric": "a",
                        }
                    ],
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["durationSeconds"] == 0.5
    assert payload["metadata"]["stems"] == [{"trackId": "vocal_1", "kind": "vocal"}]
    output = client.get(payload["outputUrl"])
    assert output.status_code == 200
    assert output.headers["content-type"] == "audio/wav"
    assert output.content.startswith(b"RIFF")
