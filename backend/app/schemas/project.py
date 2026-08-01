import re
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

GridUnit = Literal["1/4", "1/8", "1/16", "1/32"]
PITCH_PATTERN = re.compile(r"^(?P<pitch_class>[A-G](?:#|b)?)(?P<octave>-?\d+)$")
PITCH_CLASSES = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}


def pitch_to_midi(pitch: str) -> int:
    match = PITCH_PATTERN.fullmatch(pitch)
    if match is None:
        raise ValueError("pitch must use scientific pitch notation, for example C4")
    pitch_class = match.group("pitch_class")
    midi = (int(match.group("octave")) + 1) * 12 + PITCH_CLASSES[pitch_class]
    if not 0 <= midi <= 127:
        raise ValueError("pitch must be within the MIDI range C-1 to G9")
    return midi


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NoteBase(StrictModel):
    id: str = Field(min_length=1)
    pitch: str
    start: float = Field(ge=0)
    duration: float = Field(gt=0)

    @field_validator("pitch")
    @classmethod
    def validate_pitch(cls, value: str) -> str:
        pitch_to_midi(value)
        return value


class VocalNote(NoteBase):
    type: Literal["vocal"]
    lyric: str = Field(min_length=1)


class InstrumentNote(NoteBase):
    type: Literal["instrument"]
    velocity: int = Field(ge=1, le=127)


class VocalTrack(StrictModel):
    id: str = Field(min_length=1)
    type: Literal["vocal"]
    name: str = Field(min_length=1)
    voicebankId: str = Field(min_length=1)
    notes: List[VocalNote]


class InstrumentTrack(StrictModel):
    id: str = Field(min_length=1)
    type: Literal["instrument"]
    name: str = Field(min_length=1)
    instrumentId: str = Field(min_length=1)
    notes: List[InstrumentNote]


Track = Annotated[Union[VocalTrack, InstrumentTrack], Field(discriminator="type")]


class RenderRequest(StrictModel):
    projectId: str = Field(min_length=1)
    bpm: float = Field(ge=20, le=400)
    grid: GridUnit
    tracks: List[Track]
    sampleRate: int = Field(default=44100, ge=8000, le=192000)
    trackIds: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_ids(self) -> "RenderRequest":
        seen = set()
        for track in self.tracks:
            if track.id in seen:
                raise ValueError("track and note IDs must be unique")
            seen.add(track.id)
            for note in track.notes:
                if note.id in seen:
                    raise ValueError("track and note IDs must be unique")
                seen.add(note.id)

        track_ids = {track.id for track in self.tracks}
        if self.trackIds is not None:
            if len(self.trackIds) != len(set(self.trackIds)):
                raise ValueError("selected track IDs must be unique")
            unknown = set(self.trackIds) - track_ids
            if unknown:
                raise ValueError(
                    "selected track IDs are not present in the project: "
                    + ", ".join(sorted(unknown))
                )
        return self
