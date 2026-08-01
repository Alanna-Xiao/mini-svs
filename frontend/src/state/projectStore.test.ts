import { beforeEach, describe, expect, it, vi } from "vitest";

import { activeTrack, useProjectStore } from "./projectStore";

describe("project store", () => {
  beforeEach(() => {
    useProjectStore.setState({ activeTrackId: "vocal_1", selectedNoteId: "note_1" });
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
});
