import pytest
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
    yield
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
