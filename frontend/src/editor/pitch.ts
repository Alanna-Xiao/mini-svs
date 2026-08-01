const PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

export function midiToPitch(midi: number): string {
  const octave = Math.floor(midi / 12) - 1;
  return `${PITCH_CLASSES[midi % 12]}${octave}`;
}

export const VISIBLE_PITCHES = Array.from(
  { length: 60 },
  (_, index) => midiToPitch(95 - index),
);

export function isBlackKey(pitch: string): boolean {
  return pitch.includes("#");
}
