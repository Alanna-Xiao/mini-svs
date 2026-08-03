from dataclasses import dataclass
from typing import List

import numpy as np

from app.engine.audio import render_vocal_note
from app.lyrics import lyric_to_phonemes
from app.schemas.project import GridUnit, VocalNote, VocalTrack
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
        previous_transition_frames = 0
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
                    transition_frames = _transition_crossfade_frames(
                        next_note,
                        self.transition,
                        sample_rate,
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
                fade_in_frames=previous_transition_frames,
                pitch_glide_frames=round(
                    self.transition.pitch_glide_ms * sample_rate / 1000
                ),
            )
            rendered_notes.append((round(start_seconds * sample_rate), rendered))
            previous_transition_frames = transition_frames if connected else 0

        total_frames = max(start + audio.size for start, audio in rendered_notes)
        output = np.zeros(total_frames, dtype=np.float32)
        for start, audio in rendered_notes:
            output[start : start + audio.size] += audio
        return output


def _transition_crossfade_frames(
    next_note: VocalNote,
    settings: TransitionSettings,
    sample_rate: int,
    maximum_frames: int,
) -> int:
    phonemes = lyric_to_phonemes(next_note.lyric)
    starts_with_vowel = bool(phonemes and phonemes[0][0] in "aiueo")
    crossfade_ms = (
        settings.default_crossfade_ms
        if starts_with_vowel
        else settings.consonant_crossfade_ms
    )
    return min(round(crossfade_ms * sample_rate / 1000), maximum_frames)
