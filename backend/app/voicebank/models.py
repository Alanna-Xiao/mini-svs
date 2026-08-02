from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.project import pitch_to_midi
from app.schemas.responses import LicenseSummary, VoicebankSummary


class PhonemeMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    sample: str = Field(min_length=1)
    base_pitch: str = Field(alias="basePitch")
    attack_ms: int = Field(alias="attackMs", ge=0)
    loop_start_ms: float = Field(alias="loopStartMs", ge=0)
    loop_end_ms: float = Field(alias="loopEndMs", gt=0)
    release_ms: int = Field(alias="releaseMs", ge=0)

    @model_validator(mode="after")
    def validate_metadata(self) -> "PhonemeMetadata":
        pitch_to_midi(self.base_pitch)
        if self.loop_end_ms <= self.loop_start_ms:
            raise ValueError("loopEndMs must be greater than loopStartMs")
        return self


class VoicebankMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    language: str = Field(min_length=1)
    type: Literal["sample"]
    license: LicenseSummary
    phonemes: Dict[str, PhonemeMetadata]

    def summary(self) -> VoicebankSummary:
        return VoicebankSummary(
            id=self.id,
            name=self.name,
            language=self.language,
            type=self.type,
            license=self.license,
        )


@dataclass(frozen=True)
class LoadedVoicebank:
    root: Path
    metadata: VoicebankMetadata

    def sample_path(self, phoneme: str) -> Path:
        return (self.root / self.metadata.phonemes[phoneme].sample).resolve()
