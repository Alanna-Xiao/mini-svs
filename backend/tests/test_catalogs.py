import json

import pytest

from app.core.errors import MiniSvsError
from app.instruments.catalog import InstrumentCatalog
from app.voicebank.catalog import VoicebankCatalog


def voicebank_payload():
    return {
        "id": "author_demo",
        "name": "Author Demo Voice",
        "language": "ja",
        "type": "sample",
        "license": {
            "code": "custom-non-commercial",
            "summary": "Non-commercial mini-svs demo/testing use only.",
        },
        "phonemes": {
            "a": {
                "sample": "samples/a.wav",
                "basePitch": "C4",
                "attackMs": 80,
                "loopStartMs": 180,
                "loopEndMs": 620,
                "releaseMs": 120,
            }
        },
    }


def test_voicebank_catalog_lists_normalized_metadata(tmp_path):
    voicebank_dir = tmp_path / "author_demo"
    sample_dir = voicebank_dir / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "a.wav").write_bytes(b"sample fixture")
    (voicebank_dir / "voicebank.json").write_text(
        json.dumps(voicebank_payload()), encoding="utf-8"
    )

    catalog = VoicebankCatalog(tmp_path)
    assert catalog.list()[0].id == "author_demo"
    assert catalog.require("author_demo").phonemes["a"].base_pitch == "C4"


def test_voicebank_catalog_rejects_missing_samples(tmp_path):
    voicebank_dir = tmp_path / "author_demo"
    voicebank_dir.mkdir()
    (voicebank_dir / "voicebank.json").write_text(
        json.dumps(voicebank_payload()), encoding="utf-8"
    )

    with pytest.raises(MiniSvsError) as error:
        VoicebankCatalog(tmp_path).require("author_demo")
    assert error.value.code == "missing_voicebank_sample"


def test_instrument_catalog_hides_paths_and_validates_files(tmp_path):
    library = tmp_path / "piano.sf2"
    library.write_bytes(b"soundfont fixture")
    config = tmp_path / "instruments.json"
    config.write_text(
        json.dumps(
            {
                "instruments": [
                    {
                        "id": "piano",
                        "name": "Test Piano",
                        "format": "sf2",
                        "path": str(library),
                        "bank": 0,
                        "program": 0,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    catalog = InstrumentCatalog(config)
    summary = catalog.list()[0]
    assert summary.model_dump() == {"id": "piano", "name": "Test Piano", "format": "sf2"}
    assert catalog.require("piano") == summary
