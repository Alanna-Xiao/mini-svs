import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    repository_root: Path
    voicebank_dir: Path
    instrument_config: Path
    output_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    repository_root = Path(__file__).resolve().parents[3]
    return Settings(
        repository_root=repository_root,
        voicebank_dir=Path(
            os.getenv("MINI_SVS_VOICEBANK_DIR", repository_root / "voicebanks")
        ),
        instrument_config=Path(
            os.getenv(
                "MINI_SVS_INSTRUMENT_CONFIG",
                repository_root / "instruments" / "instruments.json",
            )
        ),
        output_dir=Path(
            os.getenv("MINI_SVS_OUTPUT_DIR", repository_root / "outputs")
        ),
    )
