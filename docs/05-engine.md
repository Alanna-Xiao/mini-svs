# Engine

The engine owns synthesis behavior.

## First-Version Engine

- sample-based engine using author-recorded voice samples

## Future Engine Candidates

- DiffSinger/OpenVPI adapter
- ONNX-based inference adapter
- DDSP experimental adapter

## Required Behavior

- Convert piano-roll notes into render tasks.
- Resolve romaji, hiragana, katakana, and kanji lyrics to voicebank phoneme keys.
- Ask the voicebank for the correct sample or model data.
- Match sample duration to target note duration.
- Shift pitch to target note.
- Apply amplitude envelopes.
- Connect neighboring vocal notes.
- Return rendered audio to the output module.
- Keep vocal synthesis separate from instrument rendering.
- Return deterministic metadata with each rendered buffer, including sample rate, duration, channel count, and clipping status.

## Engine Input

The engine receives validated backend schema objects, not raw frontend state.

Minimum render input:

```json
{
  "sampleRate": 44100,
  "bpm": 120,
  "grid": "1/16",
  "tracks": []
}
```

The engine may receive only selected tracks when the frontend requests stem rendering.

## Engine Output

The engine returns audio data and metadata to the output module.

Minimum render result metadata:

```json
{
  "sampleRate": 44100,
  "channels": 1,
  "durationSeconds": 2.0,
  "peakAmplitude": 0.82,
  "clipped": false,
  "stems": [
    {
      "trackId": "vocal_1",
      "kind": "vocal"
    }
  ]
}
```

The actual audio buffer is passed in memory or through a temporary internal file; API clients should receive an output ID or download URL.

## Sustained Voice Rendering

Recorded voice samples must be extended into sustained notes.

MVP algorithm:

1. Split the sample into `attack`, `sustain`, and `release` using voicebank metadata. The protected attack must include the consonant onset before the vowel loop.
2. Loop the `sustain` region until the target duration is reached.
3. Crossfade each loop boundary to avoid clicks.
4. Trim or pad to the exact note duration.
5. Pitch-shift to the requested note.
6. Apply a final amplitude envelope.

The first version may use manual loop points. Later versions can add automatic loop-point detection.

## Voice Note Transitions

mini-svs must connect neighboring vocal notes naturally.

Required behavior:

- Detect adjacent or overlapping vocal notes.
- Crossfade the end of the first note into the start of the next note.
- Smooth pitch movement between different notes.
- Preserve consonant clarity at syllable starts.
- Avoid doubling volume during overlaps.
- Avoid clicks at note boundaries.

Recommended MVP transition settings:

```json
{
  "transition": {
    "connectGapMs": 30,
    "defaultCrossfadeMs": 40,
    "consonantCrossfadeMs": 15,
    "pitchGlideMs": 35
  }
}
```

Future improvements:

- phoneme-aware transitions
- recorded transition samples
- VCV-style voicebanks
- automatic consonant/vowel boundary detection

## Failure Handling

- Missing voicebank sample: fail the render with a structured error.
- Unsupported lyric or phoneme: use a configured fallback phoneme if available, otherwise fail validation.
- A Japanese lyric is romanized before lookup; the error includes both the entered lyric and resolved phoneme when its sample is missing.
- Invalid loop points: fail voicebank validation before rendering.
- Clipping after mix/render: report `clipped: true`; output may normalize according to output settings.
