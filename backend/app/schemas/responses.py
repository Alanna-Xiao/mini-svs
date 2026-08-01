from typing import List, Literal

from pydantic import BaseModel, ConfigDict


class ResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(ResponseModel):
    status: Literal["ok"]
    version: str


class LicenseSummary(ResponseModel):
    code: str
    summary: str


class VoicebankSummary(ResponseModel):
    id: str
    name: str
    language: str
    type: str
    license: LicenseSummary


class InstrumentSummary(ResponseModel):
    id: str
    name: str
    format: Literal["sf2", "sf3", "sfz"]


class StemMetadata(ResponseModel):
    trackId: str
    kind: Literal["vocal", "instrument"]


class RenderMetadata(ResponseModel):
    sampleRate: int
    channels: int
    durationSeconds: float
    peakAmplitude: float
    clipped: bool
    stems: List[StemMetadata]


class RenderResponse(ResponseModel):
    outputId: str
    outputUrl: str
    metadata: RenderMetadata
