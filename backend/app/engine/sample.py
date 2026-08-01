from dataclasses import dataclass
from typing import List

import numpy as np

from app.engine.audio import render_vocal_note
from app.schemas.project import GridUnit, VocalTrack
from app.voicebank.models import LoadedVoicebank


@dataclass(frozen=True)
class TransitionSettings:
    connect_gap_ms: int = 30
    default_crossfade_ms: int = 40
    consonant_crossfade_ms: int = 15
    pitch_glide_ms: int = 35


def ticks_to_seconds(ticks: float, bpm: float, grid: GridUnit) -> float:
    denominator = int(grid.split("/")[1])
    beats = ticks * 4 / denominator
    return beats * 60 / bpm


class SampleEngine:
    def __init__(self, transition: TransitionSettings = TransitionSettings()) -> None:
        self.transition = transition

    def render_track(
        self,
        track: VocalTrack,
        voicebank: LoadedVoicebank,
        bpm: float,
        grid: GridUnit,
        sample_rate: int,
    ) -> np.ndarray:
        notes = sorted(track.notes, key=lambda item: (item.start, item.id))
        if not notes:
            return np.zeros(0, dtype=np.float32)

        rendered_notes: List[tuple] = []
        previous_connected = False
        for index, note in enumerate(notes):
            start_seconds = ticks_to_seconds(note.start, bpm, grid)
            duration_seconds = ticks_to_seconds(note.duration, bpm, grid)
            duration_frames = max(1, round(duration_seconds * sample_rate))
            next_note = notes[index + 1] if index + 1 < len(notes) else None
            connected = False
            transition_frames = 0
            next_pitch = None
            if next_note is not None:
                end_seconds = start_seconds + duration_seconds
                gap_ms = (ticks_to_seconds(next_note.start, bpm, grid) - end_seconds) * 1000
                connected = gap_ms <= self.transition.connect_gap_ms
                if connected:
                    transition_frames = min(
                        round(self.transition.default_crossfade_ms * sample_rate / 1000),
                        duration_frames,
                    )
                    next_pitch = next_note.pitch

            rendered = render_vocal_note(
                note,
                voicebank,
                duration_frames,
                sample_rate,
                transition_frames=transition_frames,
                next_pitch=next_pitch,
                fade_in_frames=(
                    round(self.transition.default_crossfade_ms * sample_rate / 1000)
                    if previous_connected
                    else 0
                ),
            )
            rendered_notes.append((round(start_seconds * sample_rate), rendered))
            previous_connected = connected

        total_frames = max(start + audio.size for start, audio in rendered_notes)
        output = np.zeros(total_frames, dtype=np.float32)
        for start, audio in rendered_notes:
            output[start : start + audio.size] += audio
        return output
