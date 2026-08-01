from app.core.errors import MiniSvsError
from app.instruments.catalog import InstrumentCatalog
from app.schemas.project import InstrumentTrack, RenderRequest, VocalTrack
from app.schemas.responses import RenderResponse
from app.voicebank.catalog import VoicebankCatalog


class RenderCoordinator:
    def __init__(
        self,
        voicebanks: VoicebankCatalog,
        instruments: InstrumentCatalog,
    ) -> None:
        self.voicebanks = voicebanks
        self.instruments = instruments

    def render(self, request: RenderRequest) -> RenderResponse:
        selected_ids = set(request.trackIds or [track.id for track in request.tracks])
        for track in request.tracks:
            if track.id not in selected_ids:
                continue
            if isinstance(track, VocalTrack):
                self.voicebanks.require(track.voicebankId)
            elif isinstance(track, InstrumentTrack):
                self.instruments.require(track.instrumentId)

        raise MiniSvsError(
            "engine_not_ready",
            "The sample synthesis engine has not been connected yet.",
            status_code=501,
        )
