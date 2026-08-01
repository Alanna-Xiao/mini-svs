import json
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from app.core.errors import MiniSvsError
from app.schemas.responses import InstrumentSummary


class InstrumentConfigEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    format: Literal["sf2", "sf3", "sfz"]
    path: Path

    def summary(self) -> InstrumentSummary:
        return InstrumentSummary(id=self.id, name=self.name, format=self.format)


class InstrumentCatalog:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def list(self) -> List[InstrumentSummary]:
        if not self.config_path.is_file():
            return []
        return [entry.summary() for entry in self._read()]

    def require(self, instrument_id: str) -> InstrumentSummary:
        for instrument in self._read() if self.config_path.is_file() else []:
            if instrument.id == instrument_id:
                if not instrument.path.expanduser().is_file():
                    raise MiniSvsError(
                        "missing_instrument_file",
                        f"Configured file for instrument '{instrument_id}' is missing.",
                        details={"instrumentId": instrument_id},
                    )
                return instrument.summary()
        raise MiniSvsError(
            "unknown_instrument",
            f"Instrument '{instrument_id}' is not configured.",
            status_code=404,
            details={"instrumentId": instrument_id},
        )

    def _read(self) -> List[InstrumentConfigEntry]:
        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
            return TypeAdapter(List[InstrumentConfigEntry]).validate_python(
                payload.get("instruments", [])
            )
        except (OSError, AttributeError, json.JSONDecodeError, ValidationError) as error:
            raise MiniSvsError(
                "invalid_instrument_config",
                "Could not load the instrument configuration.",
                details={"reason": str(error)},
            ) from error
