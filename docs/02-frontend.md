# Frontend

The frontend is written in TypeScript with React and Vite.

## Module Layout

```text
frontend/
  src/
    app/
    editor/
    components/
    state/
    api/
    audio/
    types/
```

## Module Responsibilities

- `app`: app shell, routing, layout, top-level providers.
- `editor`: piano roll, grid, note blocks, pitch ruler, timeline ruler, lyric editing, note geometry.
- `components`: shared UI controls.
- `state`: project state, editor state, playback state.
- `api`: calls to the Python backend.
- `audio`: frontend preview playback and waveform display.
- `types`: shared TypeScript data structures.
- Frontend modules must not call synthesis libraries directly; all synthesis and rendering go through backend APIs.

## Piano Roll Model

The editor uses a grid:

- vertical axis: pitch
- horizontal axis: time and duration
- vocal and instrument tracks may share timing rules, but they use different render paths

Example TypeScript types:

```ts
type GridUnit = "1/4" | "1/8" | "1/16" | "1/32";

type VocalNote = {
  id: string;
  type: "vocal";
  pitch: string;
  start: number;
  duration: number;
  lyric: string;
};

type InstrumentNote = {
  id: string;
  type: "instrument";
  pitch: string;
  start: number;
  duration: number;
  velocity: number;
};

type Track =
  | {
      id: string;
      type: "vocal";
      name: string;
      voicebankId: string;
      notes: VocalNote[];
    }
  | {
      id: string;
      type: "instrument";
      name: string;
      instrumentId: string;
      notes: InstrumentNote[];
    };

type Project = {
  id: string;
  bpm: number;
  grid: GridUnit;
  tracks: Track[];
};
```

Example synthesis request:

```json
{
  "projectId": "demo_project",
  "bpm": 120,
  "grid": "1/16",
  "tracks": [
    {
      "id": "vocal_1",
      "type": "vocal",
      "name": "Main Vocal",
      "voicebankId": "author_demo",
      "notes": [
        {
          "id": "note_1",
          "type": "vocal",
          "pitch": "C4",
          "start": 0,
          "duration": 4,
          "lyric": "a"
        }
      ]
    }
  ]
}
```

The backend may convert pitch names to MIDI note numbers and grid units to seconds.

## UI Requirements

- The first screen should be the usable editor, not a marketing landing page.
- The editor must support adding, moving, resizing, and selecting notes.
- The track list must support multiple vocal and instrument tracks, up to the backend project limit.
- Users must be able to rename tracks independently of the selected voicebank or instrument preset.
- Each vocal track selects its own voicebank; each instrument track selects its own instrument preset.
- Users may delete tracks, but the editor must retain at least one vocal track.
- Lyric editing must stay attached to vocal notes.
- Instrument notes must not require lyric data.
- Playback controls must preview generated audio returned by the backend.
