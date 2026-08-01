import argparse
import json
from pathlib import Path

import soundfile as sf

from app.voicebank.analyzer import analyze_sample


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a sample-based mini-svs voicebank.")
    parser.add_argument("voicebank", type=Path)
    args = parser.parse_args()

    root = args.voicebank.resolve()
    samples = root / "samples"
    source_samples = root / "source-wav"
    if not source_samples.is_dir():
        source_samples = samples
    phonemes = [path.stem for path in sorted(source_samples.glob("*.wav"))]
    if not phonemes:
        raise SystemExit(f"No WAV samples found in {samples}")

    metadata = {
        "id": root.name,
        "name": "Author Demo Voice",
        "language": "ja",
        "type": "sample",
        "license": {
            "code": "custom-non-commercial",
            "summary": "Non-commercial mini-svs demo/testing use only.",
        },
        "phonemes": {},
    }
    reports = []
    for phoneme in phonemes:
        source_path = source_samples / f"{phoneme}.wav"
        sample_path = samples / f"{phoneme}.wav"
        processed, analysis = analyze_sample(source_path, phoneme)
        sf.write(sample_path, processed, 44100, subtype="PCM_24")
        metadata["phonemes"][phoneme] = {
            "sample": f"samples/{phoneme}.wav",
            "basePitch": analysis.base_pitch,
            "attackMs": analysis.attack_ms,
            "loopStartMs": analysis.loop_start_ms,
            "loopEndMs": analysis.loop_end_ms,
            "releaseMs": analysis.release_ms,
        }
        reports.append(analysis.report())

    (root / "voicebank.json").write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    (root / "analysis-report.json").write_text(
        json.dumps({"samples": reports}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
