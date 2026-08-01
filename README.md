# mini-svs

mini-svs is a small singing voice synthesis app inspired by Vocaloid-style editors. It is a GitHub project and technical demo, not a commercial product operated by the author.

The app is planned around a piano-roll workflow:

- vertical axis: pitch
- horizontal axis: time and note length
- note blocks: lyrics, pitch, start time, and duration

Users will create vocal notes in the editor, choose a voicebank, generate audio, and export or preview the result.

## Project Status

The `0.1.0` specification is frozen. The first implementation baseline is now in development.

Implemented so far:

- modular FastAPI backend with shared project schemas
- validation for pitches, durations, selected tracks, resource IDs, and output IDs
- local voicebank and instrument catalog boundaries
- React piano-roll editor with vocal and instrument tracks
- note creation, selection, movement, resizing, deletion, and lyric editing
- sample-based vowel synthesis with looping, pitch shifting, and note transitions
- offline vocal and SoundFont instrument WAV rendering, waveform preview, playback, and stop controls
- backend, frontend, and browser workflow tests

Vocal rendering supports the phonemes installed in the selected sample voicebank. SoundFont instrument tracks render independently through FluidSynth and may be mixed with vocal tracks by the backend.

Planned first version:

- React/TypeScript piano-roll editor
- Python synthesis backend
- local voicebank loading
- offline `.wav` generation
- audio preview in the frontend

## Voicebanks

mini-svs does not bundle commercial voicebanks, third-party model weights, or third-party singer likenesses by default. Users must download and install any external voicebank according to that voicebank's own license and terms of use.

Candidate resources for local user installation:

| Resource | Notes |
| --- | --- |
| Lingyuosa DiffSinger V1 | DiffSinger voice library; CC BY-NC-SA 4.0; non-commercial use only |
| Tiger DiffSinger | DiffSinger voice library; non-commercial/personal use only; no redistribution or derivatives |
| Canary DiffSinger | DiffSinger voice library; commercial use requires written permission or a commercial license |
| OpenUTAU SVS Index | Useful index for finding DiffSinger/OpenUTAU-compatible voices |

Always verify each voicebank's original license before use. Public download does not mean redistribution, commercial use, or derivative model creation is allowed.

## Author Voice License

Any voice samples, rendered voice demos, or model weights based on the project author's own voice are separate from the source code license.

Unless explicit written permission is granted by the voice owner, the project author's voice may be used only for non-commercial demonstration, testing, and research related to mini-svs. Commercial use, resale, sublicensing, voice cloning outside mini-svs, impersonation, or redistribution as a standalone voicebank/model is not permitted.

The GPL-3.0 license in this repository applies to the source code. It does not grant commercial rights to the project author's voice, likeness, recordings, or voice model weights.

## Instrument Sounds

mini-svs should use existing instrument libraries for accompaniment instead of building instrument sounds from scratch.

Recommended resources:

| Resource | Notes |
| --- | --- |
| MuseScore General SoundFont | General MIDI instruments including piano, saxophone, strings, brass, and drums; MIT license |
| Discord SFZ GM Bank | General MIDI SFZ bank using CC0, CC-BY, or equivalent sources; verify per-instrument attribution |
| Salamander Grand Piano | High-quality piano SFZ; CC BY 3.0 |
| Philharmonia Orchestra Samples | Orchestral and saxophone WAV samples; do not redistribute as a bundled sampler |
| Virtual Playing Orchestra | SFZ/WAV orchestral library; mixed licenses, best installed locally by users |

## Specification

Implementation details are tracked as module-level files in [docs/](docs/).

That folder intentionally contains only numbered module files.

## Development

Backend:

```bash
brew install rubberband # macOS; install rubberband-cli on Linux
brew install fluid-synth # macOS; install fluidsynth on Linux
python3 -m venv .venv
.venv/bin/python -m pip install -e 'backend[dev]'
cd backend
../.venv/bin/uvicorn app.main:app --reload
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The Vite development server proxies `/api` requests to the backend at `http://127.0.0.1:8000`.

## License

Source code is licensed under GPL-3.0. See [LICENSE](./LICENSE).
