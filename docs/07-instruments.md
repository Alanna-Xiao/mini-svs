# Instruments

Instrument accompaniment should use existing sound libraries.

## Preferred Path

```text
piano-roll or MIDI-like notes -> SoundFont/SFZ renderer -> audio
```

## Recommended Resources

- MuseScore General SoundFont: SF2/SF3, General MIDI, MIT license.
- Discord SFZ GM Bank: SFZ, General MIDI, verify per-instrument attribution.
- Salamander Grand Piano: SFZ, CC BY 3.0.
- Philharmonia Orchestra Samples: WAV, useful for saxophone/orchestral testing, do not redistribute as a bundled sampler.
- Virtual Playing Orchestra: SFZ/WAV, mixed licenses, best installed locally.

## Recommended Libraries

- `pretty_midi`
- `FluidSynth` / `pyfluidsynth`
- `sfizz`

## Module Boundary

- Instrument rendering belongs to the `instruments` backend module.
- Vocal engines must not load SoundFonts or SFZ instruments directly.
- The output module may mix rendered vocal and instrument buffers after both are rendered.

## Instrument Configuration

Instrument libraries should be referenced through local user configuration:

```json
{
  "instruments": [
    {
      "id": "musescore_general",
      "name": "MuseScore General",
      "format": "sf2",
      "path": "/path/to/MuseScore_General.sf2"
    }
  ]
}
```

Repository rule:

- Do not commit third-party SoundFonts, SFZ sample libraries, or WAV sample packs unless redistribution is explicitly allowed and attribution requirements are satisfied.

## AI Fallback

- DDSP may be used as an optional experimental backend.
- For MVP, SoundFont/SFZ is preferred because it is deterministic, simpler to integrate, and easier to license.
