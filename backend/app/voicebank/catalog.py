import json
from pathlib import Path
from typing import List

from pydantic import ValidationError

from app.core.errors import MiniSvsError
from app.schemas.responses import VoicebankSummary
from app.voicebank.models import VoicebankMetadata


class VoicebankCatalog:
    def __init__(self, root: Path) -> None:
        self.root = root

    def list(self) -> List[VoicebankSummary]:
        if not self.root.is_dir():
            return []
        summaries = []
        for metadata_path in sorted(self.root.glob("*/voicebank.json")):
            try:
                summaries.append(self._read(metadata_path).summary())
            except MiniSvsError:
                continue
        return summaries

    def require(self, voicebank_id: str) -> VoicebankMetadata:
        metadata_path = self.root / voicebank_id / "voicebank.json"
        if not metadata_path.is_file():
            raise MiniSvsError(
                "unknown_voicebank",
                f"Voicebank '{voicebank_id}' is not installed.",
                status_code=404,
                details={"voicebankId": voicebank_id},
            )
        metadata = self._read(metadata_path)
        if metadata.id != voicebank_id:
            raise MiniSvsError(
                "invalid_voicebank",
                "Voicebank directory and metadata IDs do not match.",
                details={"voicebankId": voicebank_id},
            )
        for phoneme, sample in metadata.phonemes.items():
            sample_path = (metadata_path.parent / sample.sample).resolve()
            if metadata_path.parent.resolve() not in sample_path.parents:
                raise MiniSvsError(
                    "invalid_voicebank",
                    "Voicebank sample path escapes its directory.",
                    details={"voicebankId": voicebank_id, "phoneme": phoneme},
                )
            if not sample_path.is_file():
                raise MiniSvsError(
                    "missing_voicebank_sample",
                    f"Sample for phoneme '{phoneme}' is missing.",
                    details={"voicebankId": voicebank_id, "phoneme": phoneme},
                )
        return metadata

    @staticmethod
    def _read(path: Path) -> VoicebankMetadata:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return VoicebankMetadata.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValidationError) as error:
            raise MiniSvsError(
                "invalid_voicebank",
                f"Could not load voicebank metadata at '{path.name}'.",
                details={"reason": str(error)},
            ) from error
