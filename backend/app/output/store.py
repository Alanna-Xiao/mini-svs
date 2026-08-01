import re
import uuid
from pathlib import Path

import numpy as np
import soundfile as sf

from app.core.errors import MiniSvsError

OUTPUT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class OutputStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, audio: np.ndarray, sample_rate: int) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        output_id = uuid.uuid4().hex
        path = self.root / f"{output_id}.wav"
        sf.write(path, audio, sample_rate, subtype="PCM_16", format="WAV")
        return output_id

    def resolve(self, output_id: str) -> Path:
        if not OUTPUT_ID_PATTERN.fullmatch(output_id):
            raise MiniSvsError(
                "invalid_output_id", "Output IDs may contain letters, numbers, _ and -."
            )
        path = self.root / f"{output_id}.wav"
        if not path.is_file():
            raise MiniSvsError(
                "output_not_found",
                f"Output '{output_id}' does not exist.",
                status_code=404,
            )
        return path
