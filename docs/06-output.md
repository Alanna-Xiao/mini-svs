# Output

The output module receives rendered audio and handles persistence or delivery.

## Required First-Version Outputs

- `.wav` file export
- preview audio served to the frontend
- opaque output ID returned to the frontend after rendering

## Future Outputs

- separate vocal and accompaniment stems
- project package export
- rendered mixdown

## Rules

- Output code should not know how synthesis works.
- Output code should not read voicebank internals directly.
- Output code should accept audio arrays/buffers plus metadata from the engine.
- Output code should apply file naming, format encoding, and delivery policy only.
- Output code should not expose arbitrary local filesystem paths to the frontend.

## WAV Defaults

- sample rate: 44100 Hz unless overridden by project settings
- channels: mono for vocal stems, stereo allowed for mixdowns
- bit depth: 16-bit PCM for first-version exports
