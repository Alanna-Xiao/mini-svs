from typing import List, Optional

import numpy as np

from app.core.errors import MiniSvsError
from app.engine.sample import SampleEngine
from app.instruments.catalog import InstrumentCatalog
from app.output.store import OutputStore
from app.schemas.project import InstrumentTrack, RenderRequest, VocalTrack
from app.schemas.responses import (
    RenderMetadata,
    RenderResponse,
    StemMetadata,
)
from app.voicebank.catalog import VoicebankCatalog


class RenderCoordinator:
    def __init__(
        self,
        voicebanks: VoicebankCatalog,
        instruments: InstrumentCatalog,
        outputs: OutputStore,
        sample_engine: Optional[SampleEngine] = None,
    ) -> None:
        self.voicebanks = voicebanks
        self.instruments = instruments
        self.outputs = outputs
        self.sample_engine = sample_engine or SampleEngine()

    def render(self, request: RenderRequest) -> RenderResponse:
        selected_ids = set(request.trackIds or [track.id for track in request.tracks])
        buffers = []
        stems: List[StemMetadata] = []

        for track in request.tracks:
            if track.id not in selected_ids:
                continue
            if isinstance(track, VocalTrack):
                voicebank = self.voicebanks.load(track.voicebankId)
                buffers.append(
                    self.sample_engine.render_track(
                        track, voicebank, request.bpm, request.grid, request.sampleRate
                    )
                )
                stems.append(StemMetadata(trackId=track.id, kind="vocal"))
            elif isinstance(track, InstrumentTrack) and track.notes:
                self.instruments.require(track.instrumentId)
                raise MiniSvsError(
                    "instrument_engine_not_ready",
                    "Instrument rendering has not been connected yet.",
                    status_code=501,
                    details={"trackId": track.id},
                )

        audio = _mix_buffers(buffers, request.sampleRate)
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        clipped = peak > 1.0
        if clipped:
            audio = audio * (0.98 / peak)
        output_id = self.outputs.write(audio, request.sampleRate)
        metadata = RenderMetadata(
            sampleRate=request.sampleRate,
            channels=1,
            durationSeconds=round(audio.size / request.sampleRate, 6),
            peakAmplitude=round(peak, 6),
            clipped=clipped,
            stems=stems,
        )
        return RenderResponse(
            outputId=output_id,
            outputUrl=f"/outputs/{output_id}",
            metadata=metadata,
        )


def _mix_buffers(buffers: List[np.ndarray], sample_rate: int) -> np.ndarray:
    if not buffers:
        return np.zeros(round(sample_rate * 0.1), dtype=np.float32)
    total_frames = max(buffer.size for buffer in buffers)
    mix = np.zeros(total_frames, dtype=np.float32)
    for buffer in buffers:
        mix[: buffer.size] += buffer
    return mix
