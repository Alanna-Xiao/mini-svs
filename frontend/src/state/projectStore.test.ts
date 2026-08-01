import { beforeEach, describe, expect, it, vi } from "vitest";

import { activeTrack, useProjectStore } from "./projectStore";

const initialState = useProjectStore.getState();

describe("project store", () => {
  beforeEach(() => {
    useProjectStore.setState(
      { ...initialState, project: structuredClone(initialState.project) },
      true,
    );
  });

  it("updates the selected note without changing its type", () => {
    useProjectStore.getState().updateNote("note_1", { lyric: "ka", duration: 8 });
    const track = activeTrack(useProjectStore.getState());
    const note = track.notes.find((item) => item.id === "note_1");
    expect(note).toMatchObject({ type: "vocal", lyric: "ka", duration: 8 });
  });

  it("adds a vocal note to the active track", () => {
    vi.stubGlobal("crypto", { randomUUID: () => "new_note" });
    useProjectStore.getState().addNote("D4", 12);
    const track = activeTrack(useProjectStore.getState());
    expect(track.notes.at(-1)).toMatchObject({ id: "new_note", pitch: "D4", start: 12 });
    vi.unstubAllGlobals();
  });

  it("selects and deletes multiple notes from the active track", () => {
    const store = useProjectStore.getState();
    store.selectNote("note_2", true);
    expect(useProjectStore.getState().selectedNoteIds).toEqual(["note_1", "note_2"]);

    useProjectStore.getState().deleteSelectedNotes();

    expect(activeTrack(useProjectStore.getState()).notes.map((note) => note.id)).not.toContain(
      "note_1",
    );
    expect(activeTrack(useProjectStore.getState()).notes.map((note) => note.id)).not.toContain(
      "note_2",
    );
    expect(useProjectStore.getState().selectedNoteIds).toEqual([]);
  });

  it("changes the sound assigned to an instrument track", () => {
    useProjectStore.getState().setTrackInstrument(
      "instrument_1",
      "musescore_alto_sax",
      "Alto Saxophone",
    );

    const track = useProjectStore
      .getState()
      .project.tracks.find((item) => item.id === "instrument_1");
    expect(track).toMatchObject({
      type: "instrument",
      instrumentId: "musescore_alto_sax",
      name: "1 Alto Saxophone",
    });
  });

  it("adds and removes an independent instrument track", () => {
    vi.stubGlobal("crypto", { randomUUID: () => "sax_track" });
    useProjectStore
      .getState()
      .addInstrumentTrack("musescore_alto_sax", "Alto Saxophone");

    expect(useProjectStore.getState().activeTrackId).toBe("instrument_sax_track");
    expect(activeTrack(useProjectStore.getState())).toMatchObject({
      type: "instrument",
      instrumentId: "musescore_alto_sax",
      notes: [],
    });

    useProjectStore.getState().addNote("D4", 4);
    expect(activeTrack(useProjectStore.getState()).notes).toHaveLength(1);

    useProjectStore.getState().deleteInstrumentTrack("instrument_sax_track");
    expect(useProjectStore.getState().project.tracks).toHaveLength(2);
    expect(useProjectStore.getState().activeTrackId).toBe("vocal_1");
    vi.unstubAllGlobals();
  });

  it("does not delete the vocal track", () => {
    useProjectStore.getState().deleteInstrumentTrack("vocal_1");
    expect(useProjectStore.getState().project.tracks).toHaveLength(2);
  });
});
