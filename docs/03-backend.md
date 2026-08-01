# Backend

The backend is written in Python.

## Module Layout

```text
backend/
  app/
    api/
    schemas/
    core/
    voicebank/
    engine/
    output/
    audio/
    instruments/
    storage/
```

## Module Responsibilities

- `api`: HTTP endpoints such as health checks, synthesis requests, voicebank listing, and output downloads.
- `schemas`: Pydantic request and response models.
- `core`: configuration, paths, errors, and app-level utilities.
- `voicebank`: voicebank loading, validation, metadata, sample lookup, and license metadata.
- `engine`: synthesis orchestration and engine implementations.
- `output`: `.wav` writing, preview file serving, stems, and export formats.
- `audio`: reusable low-level audio utilities such as envelopes, crossfades, pitch conversion, and resampling.
- `instruments`: accompaniment rendering with SoundFont/SFZ tools.
- `storage`: project files, user configuration, generated output paths, and local asset path resolution.

## API Requirements

Required first-version endpoints:

- `GET /health`: report backend availability.
- `GET /voicebanks`: list installed local voicebanks and their display metadata.
- `GET /instruments`: list configured local instrument libraries or presets.
- `POST /render`: render a project or selected tracks.
- `GET /outputs/{output_id}`: download or preview a rendered output.

API rules:

- Request and response bodies must use Pydantic schemas.
- Paths returned to the frontend must be safe public/download URLs or opaque IDs, not arbitrary filesystem paths.
- Backend validation must reject unknown voicebank IDs, unknown instrument IDs, invalid pitches, negative durations, and duplicate IDs.
- Rendering errors must return structured error responses instead of raw tracebacks.
