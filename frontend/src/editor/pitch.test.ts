import { describe, expect, it } from "vitest";

import { midiToPitch, VISIBLE_PITCHES } from "./pitch";

describe("pitch helpers", () => {
  it("uses scientific pitch notation", () => {
    expect(midiToPitch(60)).toBe("C4");
    expect(midiToPitch(69)).toBe("A4");
  });

  it("orders piano roll pitches from high to low", () => {
    expect(VISIBLE_PITCHES[0]).toBe("B6");
    expect(VISIBLE_PITCHES.at(-1)).toBe("C2");
  });
});
