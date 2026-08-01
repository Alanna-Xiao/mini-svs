# Voicebank

Voicebanks provide materials and metadata to engines.

## Supported First-Version Voicebank

- sample-based author demo voicebank

## Potential Future Voicebanks

- DiffSinger/OpenUTAU-compatible model voicebanks
- VCV-style sample voicebanks
- external user-installed models

## Example Metadata

```json
{
  "id": "author_demo",
  "name": "Author Demo Voice",
  "language": "ja",
  "type": "sample",
  "license": {
    "code": "custom-non-commercial",
    "summary": "Non-commercial mini-svs demo/testing use only."
  },
  "phonemes": {
    "a": {
      "sample": "samples/a.wav",
      "basePitch": "C4",
      "attackMs": 80,
      "loopStartMs": 180,
      "loopEndMs": 620,
      "releaseMs": 120
    }
  }
}
```

## Requirements

- Load short recorded samples such as vowels or CV syllables.
- Store or expose base pitch for each sample.
- Store loop points for sustained rendering.
- Store license and usage restrictions.
- Provide phoneme or lyric lookup for the engine.
- Validate that referenced sample/model paths exist before rendering.
- Expose normalized metadata to the engine; do not make the engine parse raw voicebank files directly.
- Do not write rendered audio. Rendering belongs to the engine and output modules.

## Local Directory Rules

Recommended user-local voicebank layout:

```text
voicebanks/
  author_demo/
    voicebank.json
    samples/
      a.wav
      i.wav
      u.wav
```

Repository rule:

- Do not commit voicebank samples or third-party model weights unless their license explicitly allows redistribution and the project intentionally accepts that license.
- Keep local voicebank directories ignored by git by default when implementation begins.
