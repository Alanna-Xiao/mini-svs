import { useEffect, useRef } from "react";

import { useProjectStore } from "../state/projectStore";
import type { Note } from "../types/project";
import { VISIBLE_PITCHES } from "./pitch";

export const CELL_WIDTH = 28;
export const ROW_HEIGHT = 26;

type DragMode = "move" | "resize";

type NoteBlockProps = {
  note: Note;
  selected: boolean;
};

export function NoteBlock({ note, selected }: NoteBlockProps) {
  const selectNote = useProjectStore((state) => state.selectNote);
  const updateNote = useProjectStore((state) => state.updateNote);
  const drag = useRef<{
    mode: DragMode;
    pointerX: number;
    pointerY: number;
    start: number;
    duration: number;
    pitchIndex: number;
  } | null>(null);

  useEffect(() => {
    const onMove = (event: PointerEvent) => {
      const origin = drag.current;
      if (!origin) return;
      const tickDelta = Math.round((event.clientX - origin.pointerX) / CELL_WIDTH);
      if (origin.mode === "resize") {
        updateNote(note.id, { duration: Math.max(1, origin.duration + tickDelta) });
        return;
      }
      const rowDelta = Math.round((event.clientY - origin.pointerY) / ROW_HEIGHT);
      const pitchIndex = Math.min(
        VISIBLE_PITCHES.length - 1,
        Math.max(0, origin.pitchIndex + rowDelta),
      );
      updateNote(note.id, {
        start: Math.max(0, origin.start + tickDelta),
        pitch: VISIBLE_PITCHES[pitchIndex],
      });
    };
    const onUp = () => {
      drag.current = null;
      document.body.classList.remove("dragging-note");
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, [note.id, updateNote]);

  const startDrag = (event: React.PointerEvent, mode: DragMode) => {
    event.stopPropagation();
    const additive = event.shiftKey || event.ctrlKey || event.metaKey;
    selectNote(note.id, additive);
    if (additive) return;
    drag.current = {
      mode,
      pointerX: event.clientX,
      pointerY: event.clientY,
      start: note.start,
      duration: note.duration,
      pitchIndex: VISIBLE_PITCHES.indexOf(note.pitch),
    };
    document.body.classList.add("dragging-note");
  };

  const top = VISIBLE_PITCHES.indexOf(note.pitch) * ROW_HEIGHT + 2;
  return (
    <div
      className={`note-block note-${note.type}${selected ? " selected" : ""}`}
      style={{ left: note.start * CELL_WIDTH + 1, top, width: note.duration * CELL_WIDTH - 2 }}
      onPointerDown={(event) => startDrag(event, "move")}
      onClick={(event) => event.stopPropagation()}
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      aria-label={`${note.pitch} ${note.type === "vocal" ? note.lyric : "instrument note"}`}
    >
      <span>{note.type === "vocal" ? note.lyric : note.pitch}</span>
      <button
        className="resize-handle"
        aria-label="Resize note"
        title="Resize note"
        onPointerDown={(event) => startDrag(event, "resize")}
      />
    </div>
  );
}
