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
  setTrackInstrument: (trackId: string, instrumentId: string, name: string) => void;
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
    name: "Main Vocal",
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
    name: "Piano",
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
  setTrackInstrument: (trackId, instrumentId, name) =>
    set((state) => ({
      project: {
        ...state.project,
        tracks: state.project.tracks.map((track) =>
          track.id === trackId && track.type === "instrument"
            ? { ...track, instrumentId, name }
            : track,
        ),
      },
    })),
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
