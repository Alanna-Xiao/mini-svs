import { create } from "zustand";

import type { GridUnit, Note, Project, Track } from "../types/project";

type NotePatch = Partial<{
  pitch: string;
  start: number;
  duration: number;
  lyric: string;
  velocity: number;
}>;

type ProjectState = {
  project: Project;
  activeTrackId: string;
  selectedNoteId: string | null;
  selectedNoteIds: string[];
  setBpm: (bpm: number) => void;
  setGrid: (grid: GridUnit) => void;
  setActiveTrack: (trackId: string) => void;
  setTrackName: (trackId: string, name: string) => void;
  moveTrack: (trackId: string, direction: -1 | 1) => void;
  setTrackInstrument: (trackId: string, instrumentId: string) => void;
  setTrackVoicebank: (trackId: string, voicebankId: string) => void;
  addInstrumentTrack: (instrumentId: string, name: string) => void;
  addVocalTrack: (voicebankId: string) => void;
  deleteTrack: (trackId: string) => void;
  selectNote: (noteId: string | null, additive?: boolean) => void;
  selectAllNotes: () => void;
  addNote: (pitch: string, start: number) => void;
  updateNote: (noteId: string, patch: NotePatch) => void;
  deleteSelectedNotes: () => void;
};

const initialTracks: Track[] = [
  {
    id: "vocal_1",
    type: "vocal",
    name: "1 Main Vocal",
    voicebankId: "author_demo",
    notes: [
      { id: "note_1", type: "vocal", pitch: "G3", start: 0, duration: 4, lyric: "a" },
      { id: "note_2", type: "vocal", pitch: "A3", start: 4, duration: 4, lyric: "i" },
      { id: "note_3", type: "vocal", pitch: "B3", start: 8, duration: 8, lyric: "u" },
    ],
  },
  {
    id: "instrument_1",
    type: "instrument",
    name: "2 Piano",
    instrumentId: "musescore_general",
    notes: [
      { id: "piano_c", type: "instrument", pitch: "C4", start: 0, duration: 8, velocity: 96 },
      { id: "piano_e", type: "instrument", pitch: "E4", start: 0, duration: 8, velocity: 96 },
      { id: "piano_g", type: "instrument", pitch: "G4", start: 0, duration: 8, velocity: 96 },
    ],
  },
];

function mapActiveTrack(
  tracks: Track[],
  activeTrackId: string,
  transform: (track: Track) => Track,
): Track[] {
  return tracks.map((track) => (track.id === activeTrackId ? transform(track) : track));
}

function nextTrackNumber(tracks: Track[]): number {
  const used = new Set(
    tracks
      .map((track) => Number(track.name.match(/^(\d+) /)?.[1]))
      .filter((number) => Number.isInteger(number) && number > 0),
  );
  let number = 1;
  while (used.has(number)) number += 1;
  return number;
}

export const useProjectStore = create<ProjectState>((set) => ({
  project: {
    projectId: "untitled_project",
    bpm: 120,
    grid: "1/16",
    sampleRate: 44100,
    tracks: initialTracks,
  },
  activeTrackId: "vocal_1",
  selectedNoteId: "note_1",
  selectedNoteIds: ["note_1"],
  setBpm: (bpm) =>
    set((state) => ({ project: { ...state.project, bpm: Math.min(400, Math.max(20, bpm)) } })),
  setGrid: (grid) => set((state) => ({ project: { ...state.project, grid } })),
  setActiveTrack: (activeTrackId) =>
    set({ activeTrackId, selectedNoteId: null, selectedNoteIds: [] }),
  setTrackName: (trackId, name) =>
    set((state) => ({
      project: {
        ...state.project,
        tracks: state.project.tracks.map((track) =>
          track.id === trackId ? { ...track, name: name.slice(0, 64) } : track,
        ),
      },
    })),
  moveTrack: (trackId, direction) =>
    set((state) => {
      const index = state.project.tracks.findIndex((track) => track.id === trackId);
      const targetIndex = index + direction;
      if (index < 0 || targetIndex < 0 || targetIndex >= state.project.tracks.length) {
        return state;
      }
      const tracks = [...state.project.tracks];
      [tracks[index], tracks[targetIndex]] = [tracks[targetIndex], tracks[index]];
      return { project: { ...state.project, tracks } };
    }),
  setTrackInstrument: (trackId, instrumentId) =>
    set((state) => ({
      project: {
        ...state.project,
        tracks: state.project.tracks.map((track) =>
          track.id === trackId && track.type === "instrument"
            ? { ...track, instrumentId }
            : track,
        ),
      },
    })),
  setTrackVoicebank: (trackId, voicebankId) =>
    set((state) => ({
      project: {
        ...state.project,
        tracks: state.project.tracks.map((track) =>
          track.id === trackId && track.type === "vocal" ? { ...track, voicebankId } : track,
        ),
      },
    })),
  addInstrumentTrack: (instrumentId, name) =>
    set((state) => {
      if (state.project.tracks.length >= 16) return state;
      const id = `instrument_${crypto.randomUUID()}`;
      const instrumentNumber = nextTrackNumber(state.project.tracks);
      const track: Track = {
        id,
        type: "instrument",
        name: `${instrumentNumber} ${name}`,
        instrumentId,
        notes: [],
      };
      return {
        project: { ...state.project, tracks: [...state.project.tracks, track] },
        activeTrackId: id,
        selectedNoteId: null,
        selectedNoteIds: [],
      };
    }),
  addVocalTrack: (voicebankId) =>
    set((state) => {
      if (state.project.tracks.length >= 16) return state;
      const id = `vocal_${crypto.randomUUID()}`;
      const vocalNumber = nextTrackNumber(state.project.tracks);
      const track: Track = {
        id,
        type: "vocal",
        name: `${vocalNumber} Vocal`,
        voicebankId,
        notes: [],
      };
      return {
        project: { ...state.project, tracks: [...state.project.tracks, track] },
        activeTrackId: id,
        selectedNoteId: null,
        selectedNoteIds: [],
      };
    }),
  deleteTrack: (trackId) =>
    set((state) => {
      const target = state.project.tracks.find((track) => track.id === trackId);
      if (!target) return state;
      const vocalCount = state.project.tracks.filter((track) => track.type === "vocal").length;
      if (target.type === "vocal" && vocalCount <= 1) return state;
      const tracks = state.project.tracks.filter((track) => track.id !== trackId);
      const activeTrackId =
        state.activeTrackId === trackId ? tracks[0]?.id ?? state.activeTrackId : state.activeTrackId;
      return {
        project: { ...state.project, tracks },
        activeTrackId,
        selectedNoteId: state.activeTrackId === trackId ? null : state.selectedNoteId,
        selectedNoteIds: state.activeTrackId === trackId ? [] : state.selectedNoteIds,
      };
    }),
  selectNote: (noteId, additive = false) =>
    set((state) => {
      if (noteId === null) return { selectedNoteId: null, selectedNoteIds: [] };
      if (!additive) return { selectedNoteId: noteId, selectedNoteIds: [noteId] };
      const selected = state.selectedNoteIds.includes(noteId);
      const selectedNoteIds = selected
        ? state.selectedNoteIds.filter((id) => id !== noteId)
        : [...state.selectedNoteIds, noteId];
      return {
        selectedNoteId: selected
          ? selectedNoteIds.at(-1) ?? null
          : noteId,
        selectedNoteIds,
      };
    }),
  selectAllNotes: () =>
    set((state) => {
      const noteIds = activeTrack(state).notes.map((note) => note.id);
      return {
        selectedNoteId: noteIds.at(-1) ?? null,
        selectedNoteIds: noteIds,
      };
    }),
  addNote: (pitch, start) =>
    set((state) => {
      const id = crypto.randomUUID();
      const tracks = mapActiveTrack(state.project.tracks, state.activeTrackId, (track) => {
        if (track.type === "vocal") {
          return {
            ...track,
            notes: [...track.notes, { id, type: "vocal", pitch, start, duration: 4, lyric: "a" }],
          };
        }
        return {
          ...track,
          notes: [...track.notes, { id, type: "instrument", pitch, start, duration: 4, velocity: 96 }],
        };
      });
      return {
        project: { ...state.project, tracks },
        selectedNoteId: id,
        selectedNoteIds: [id],
      };
    }),
  updateNote: (noteId, patch) =>
    set((state) => ({
      project: {
        ...state.project,
        tracks: mapActiveTrack(state.project.tracks, state.activeTrackId, (track) => ({
          ...track,
          notes: track.notes.map((note) =>
            note.id === noteId ? ({ ...note, ...patch } as typeof note) : note,
          ),
        }) as Track),
      },
    })),
  deleteSelectedNotes: () =>
    set((state) => {
      if (state.selectedNoteIds.length === 0) return state;
      const selected = new Set(state.selectedNoteIds);
      return {
        project: {
          ...state.project,
          tracks: mapActiveTrack(state.project.tracks, state.activeTrackId, (track) => ({
            ...track,
            notes: track.notes.filter((note) => !selected.has(note.id)),
          }) as Track),
        },
        selectedNoteId: null,
        selectedNoteIds: [],
      };
    }),
}));

export function activeTrack(state: ProjectState): Track {
  return state.project.tracks.find((track) => track.id === state.activeTrackId) ?? state.project.tracks[0];
}

export function selectedNote(state: ProjectState): Note | null {
  const track = activeTrack(state);
  return track.notes.find((note) => note.id === state.selectedNoteId) ?? null;
}
