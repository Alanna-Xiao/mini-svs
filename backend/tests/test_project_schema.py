import pytest
from pydantic import ValidationError

from app.schemas.project import RenderRequest, pitch_to_midi


def project_payload():
    return {
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
                        "pitch": "C4",
                        "start": 0,
                        "duration": 4,
                        "lyric": "a",
                    }
                ],
            }
        ],
    }


def test_pitch_to_midi():
    assert pitch_to_midi("C4") == 60
    assert pitch_to_midi("Bb3") == 58
    assert pitch_to_midi("C-1") == 0


@pytest.mark.parametrize("pitch", ["H4", "C10", "c4", "60"])
def test_rejects_invalid_pitch(pitch):
    payload = project_payload()
    payload["tracks"][0]["notes"][0]["pitch"] = pitch
    with pytest.raises(ValidationError):
        RenderRequest.model_validate(payload)


def test_rejects_duplicate_ids():
    payload = project_payload()
    payload["tracks"][0]["notes"][0]["id"] = "vocal_1"
    with pytest.raises(ValidationError, match="must be unique"):
        RenderRequest.model_validate(payload)


def test_rejects_negative_duration():
    payload = project_payload()
    payload["tracks"][0]["notes"][0]["duration"] = -1
    with pytest.raises(ValidationError):
        RenderRequest.model_validate(payload)


def test_rejects_projects_longer_than_five_minutes():
    payload = project_payload()
    payload["tracks"][0]["notes"][0]["duration"] = 2401
    with pytest.raises(ValidationError, match="may not exceed 300 seconds"):
        RenderRequest.model_validate(payload)


def test_rejects_oversized_lyrics():
    payload = project_payload()
    payload["tracks"][0]["notes"][0]["lyric"] = "a" * 33
    with pytest.raises(ValidationError):
        RenderRequest.model_validate(payload)
