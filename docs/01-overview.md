# Overview

mini-svs is a singing voice synthesis app for GitHub release. It is intended as a technical demo, not as a commercial product operated by the author.

## Specification Status

- Version: `0.2.0`
- Status: Active
- Revised on: `2026-08-06`
- Previous baseline tag: `spec-v0.1.0`

This active revision supersedes the `0.1.0` baseline. Functional or architectural changes require an explicit spec revision and version update; a new spec tag is created when the revision is frozen. Editorial corrections that do not change behavior may be committed without changing the spec version.

## Spec Files

This spec is split by module:

- `01-overview.md`: project goals, stack, and architecture.
- `02-frontend.md`: TypeScript frontend and piano-roll data model.
- `03-backend.md`: Python backend modules and APIs.
- `04-voicebank.md`: voicebank metadata and local asset rules.
- `05-engine.md`: synthesis engine, sustained notes, and transitions.
- `06-output.md`: export and preview output.
- `07-instruments.md`: accompaniment instruments and rendering.
- `08-licensing.md`: source, voice, and third-party asset licensing.
- `09-deployment.md`: Cloudflare Worker, Tunnel, local service, and security boundaries.

## Goals

- Provide a Vocaloid-like piano-roll editing workflow.
- Use Python for synthesis, audio processing, and backend APIs.
- Use TypeScript for the frontend editor and playback UI.
- Prefer existing libraries and compatible models over rebuilding solved systems.
- Keep source code, voicebanks, engine logic, and output logic modular.
- Keep voice, instrument, project, and rendered output assets outside git unless explicitly safe to redistribute.

## Non-Goals For The First Version

- Commercial distribution of the author's voice assets.
- Training a custom AI singing model from scratch.
- Bundling commercial or unclear-license voicebanks.
- Real-time DAW plugin support.

## Technology Stack

Backend:

- Python
- FastAPI
- Pydantic
- NumPy
- SciPy
- soundfile
- librosa
- pretty_midi
- FluidSynth / pyfluidsynth
- PyYAML

Frontend:

- TypeScript
- React
- Vite
- Zustand
- wavesurfer.js
- lucide-react

Optional future backend dependencies:

- torch
- torchaudio
- onnxruntime
- sfizz
- DDSP

System dependencies:

- FluidSynth binary/library for SoundFont rendering.
- libsndfile for robust audio file reading and writing.

## Core Architecture

The synthesis path is split into three independent layers:

```text
Voicebank -> Engine -> Output
```

Responsibilities:

- `Voicebank`: stores metadata, samples, model paths, phoneme mappings, loop points, and license information.
- `Engine`: reads project notes, calls the selected voicebank, handles duration matching, pitch handling, transitions, and synthesis.
- `Output`: receives rendered audio from the engine and writes or serves the result, such as `.wav`, preview audio, stems, or exported project files.

Boundary rules:

- A voicebank must not render final audio by itself.
- An engine must not own voicebank license metadata or stored samples.
- Output code must not contain synthesis logic.
- Instrument rendering must stay separate from vocal synthesis. A mixdown may combine their rendered audio after both tracks are rendered.
- API request/response schemas are the contract between frontend and backend; module internals should not leak through API payloads.

## Runtime Architecture

The public frontend and API gateway run on Cloudflare Workers. The synthesis backend, voicebank, instrument libraries, and generated output stay on the author's Mac and are reached through Cloudflare Tunnel. This deployment choice avoids paid Containers and does not change the core `Voicebank -> Engine -> Output` module boundary.
