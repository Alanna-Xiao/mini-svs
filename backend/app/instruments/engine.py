import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pretty_midi
import soundfile as sf

from app.core.errors import MiniSvsError
from app.engine.sample import ticks_to_seconds
from app.instruments.catalog import InstrumentConfigEntry
from app.schemas.project import GridUnit, InstrumentTrack, pitch_to_midi


class InstrumentEngine:
    def render_track(
        self,
        track: InstrumentTrack,
        instrument: InstrumentConfigEntry,
        bpm: float,
        grid: GridUnit,
        sample_rate: int,
    ) -> np.ndarray:
        if not track.notes:
            return np.zeros(0, dtype=np.float32)
        executable = shutil.which("fluidsynth")
        if executable is None:
            raise MiniSvsError(
                "instrument_engine_unavailable",
                "FluidSynth is required to render SoundFont instruments.",
            )

        midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
        preset = pretty_midi.Instrument(program=instrument.program, name=track.name)
        preset.control_changes.extend(
            [
                pretty_midi.ControlChange(number=0, value=instrument.bank >> 7, time=0),
                pretty_midi.ControlChange(number=32, value=instrument.bank & 127, time=0),
            ]
        )
        for note in sorted(track.notes, key=lambda item: (item.start, item.id)):
            start = ticks_to_seconds(note.start, bpm, grid)
            end = start + ticks_to_seconds(note.duration, bpm, grid)
            preset.notes.append(
                pretty_midi.Note(
                    velocity=note.velocity,
                    pitch=pitch_to_midi(note.pitch),
                    start=start,
                    end=end,
                )
            )
        midi.instruments.append(preset)

        with tempfile.TemporaryDirectory(prefix="mini-svs-instrument-") as directory:
            midi_path = Path(directory) / "track.mid"
            output_path = Path(directory) / "track.wav"
            midi.write(str(midi_path))
            command = [
                executable,
                "-niq",
                "-r",
                str(sample_rate),
                "-g",
                "0.6",
                "-F",
                str(output_path),
                "-T",
                "wav",
                str(instrument.path.expanduser()),
                str(midi_path),
            ]
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
                audio, rendered_rate = sf.read(
                    output_path, dtype="float32", always_2d=False
                )
            except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
                reason = (
                    error.stderr.strip()
                    if isinstance(error, subprocess.CalledProcessError)
                    else str(error)
                )
                raise MiniSvsError(
                    "instrument_render_failed",
                    f"Could not render instrument track '{track.id}'.",
                    details={"reason": reason},
                ) from error

        if rendered_rate != sample_rate:
            raise MiniSvsError(
                "instrument_render_failed",
                "FluidSynth returned audio at an unexpected sample rate.",
            )
        if audio.ndim == 2:
            audio = np.mean(audio, axis=1)
        return np.asarray(audio, dtype=np.float32)
