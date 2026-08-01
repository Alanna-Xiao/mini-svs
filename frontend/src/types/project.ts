export type GridUnit = "1/4" | "1/8" | "1/16" | "1/32";

export type VocalNote = {
  id: string;
  type: "vocal";
  pitch: string;
  start: number;
  duration: number;
  lyric: string;
};

export type InstrumentNote = {
  id: string;
  type: "instrument";
  pitch: string;
  start: number;
  duration: number;
  velocity: number;
};

export type Note = VocalNote | InstrumentNote;

export type VocalTrack = {
  id: string;
  type: "vocal";
  name: string;
  voicebankId: string;
  notes: VocalNote[];
};

export type InstrumentTrack = {
  id: string;
  type: "instrument";
  name: string;
  instrumentId: string;
  notes: InstrumentNote[];
};

export type Track = VocalTrack | InstrumentTrack;

export type Project = {
  projectId: string;
  bpm: number;
  grid: GridUnit;
  sampleRate: number;
  tracks: Track[];
};

export type RenderMetadata = {
  sampleRate: number;
  channels: number;
  durationSeconds: number;
  peakAmplitude: number;
  clipped: boolean;
  stems: Array<{ trackId: string; kind: "vocal" | "instrument" }>;
};

export type RenderResponse = {
  outputId: string;
  outputUrl: string;
  metadata: RenderMetadata;
};
