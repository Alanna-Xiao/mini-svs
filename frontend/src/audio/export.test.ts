import { describe, expect, it } from "vitest";

import { wavFileName } from "./export";

describe("wavFileName", () => {
  it("creates a filesystem-safe WAV name", () => {
    expect(wavFileName("My first song / demo")).toBe("My-first-song-demo.wav");
  });

  it("uses a fallback when the project id has no safe characters", () => {
    expect(wavFileName(" 音楽 ")).toBe("mini-svs-project.wav");
  });
});
