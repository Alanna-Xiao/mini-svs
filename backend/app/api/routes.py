from pathlib import Path
from typing import List

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.errors import MiniSvsError
from app.engine.service import RenderCoordinator
from app.instruments.catalog import InstrumentCatalog
from app.output.store import OutputStore
from app.schemas.project import RenderRequest
from app.schemas.responses import (
    HealthResponse,
    InstrumentSummary,
    RenderResponse,
    VoicebankSummary,
)
from app.voicebank.catalog import VoicebankCatalog

router = APIRouter()


def voicebank_catalog() -> VoicebankCatalog:
    return VoicebankCatalog(get_settings().voicebank_dir)


def instrument_catalog() -> InstrumentCatalog:
    return InstrumentCatalog(get_settings().instrument_config)


def output_store() -> OutputStore:
    return OutputStore(get_settings().output_dir)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/voicebanks", response_model=List[VoicebankSummary])
def list_voicebanks() -> List[VoicebankSummary]:
    return voicebank_catalog().list()


@router.get("/instruments", response_model=List[InstrumentSummary])
def list_instruments() -> List[InstrumentSummary]:
    return instrument_catalog().list()


@router.post("/render", response_model=RenderResponse)
def render(request: RenderRequest) -> RenderResponse:
    coordinator = RenderCoordinator(voicebank_catalog(), instrument_catalog())
    return coordinator.render(request)


@router.get("/outputs/{output_id:path}")
def get_output(output_id: str) -> FileResponse:
    path: Path = output_store().resolve(output_id)
    return FileResponse(path, media_type="audio/wav", filename=path.name)
