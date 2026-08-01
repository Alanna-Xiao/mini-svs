import { beforeEach, describe, expect, it, vi } from "vitest";

import { activeTrack, useProjectStore } from "./projectStore";

describe("project store", () => {
  beforeEach(() => {
    useProjectStore.setState({
      activeTrackId: "vocal_1",
      selectedNoteId: "note_1",
      selectedNoteIds: ["note_1"],
    });
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
      name: "Alto Saxophone",
    });
  });
});
