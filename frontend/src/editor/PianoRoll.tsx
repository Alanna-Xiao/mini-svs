import { useEffect, useLayoutEffect, useRef } from "react";

import { activeTrack, useProjectStore } from "../state/projectStore";
import { CELL_WIDTH, NoteBlock, ROW_HEIGHT } from "./NoteBlock";
import { isBlackKey, VISIBLE_PITCHES } from "./pitch";

const TOTAL_TICKS = 96;

export function PianoRoll() {
  const timelineRef = useRef<HTMLDivElement>(null);
  const pitchRulerRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const track = useProjectStore(activeTrack);
  const selectedNoteIds = useProjectStore((state) => state.selectedNoteIds);
  const addNote = useProjectStore((state) => state.addNote);
  const selectNote = useProjectStore((state) => state.selectNote);
  const selectAllNotes = useProjectStore((state) => state.selectAllNotes);
  const deleteSelectedNotes = useProjectStore((state) => state.deleteSelectedNotes);

  useLayoutEffect(() => {
    const initialPitchRegion = Math.max(0, VISIBLE_PITCHES.indexOf("E4") * ROW_HEIGHT);
    if (scrollRef.current) scrollRef.current.scrollTop = initialPitchRegion;
    if (pitchRulerRef.current) pitchRulerRef.current.scrollTop = initialPitchRegion;
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const editing =
        target?.matches("input, textarea, select") || target?.isContentEditable;
      if (editing) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "a") {
        event.preventDefault();
        selectAllNotes();
      } else if (event.key === "Delete" || event.key === "Backspace") {
        event.preventDefault();
        deleteSelectedNotes();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [deleteSelectedNotes, selectAllNotes]);

  const addAtPointer = (event: React.MouseEvent<HTMLDivElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const start = Math.max(0, Math.floor((event.clientX - bounds.left) / CELL_WIDTH));
    const row = Math.min(
      VISIBLE_PITCHES.length - 1,
      Math.max(0, Math.floor((event.clientY - bounds.top) / ROW_HEIGHT)),
    );
    addNote(VISIBLE_PITCHES[row], start);
  };

  return (
    <div className="piano-roll" data-track-type={track.type}>
      <div className="timeline-corner" />
      <div className="timeline" ref={timelineRef}>
        <div className="timeline-content" style={{ width: TOTAL_TICKS * CELL_WIDTH }}>
          {Array.from({ length: TOTAL_TICKS / 4 }, (_, index) => (
            <span key={index} style={{ left: index * CELL_WIDTH * 4 }}>
              {index + 1}
            </span>
          ))}
        </div>
      </div>
      <div className="pitch-ruler" ref={pitchRulerRef}>
        {VISIBLE_PITCHES.map((pitch) => (
          <div className={isBlackKey(pitch) ? "black-key" : "white-key"} key={pitch}>
            {pitch.startsWith("C") ? pitch : ""}
          </div>
        ))}
      </div>
      <div
        className="roll-scroll"
        ref={scrollRef}
        onScroll={(event) => {
          if (timelineRef.current) timelineRef.current.scrollLeft = event.currentTarget.scrollLeft;
          if (pitchRulerRef.current) pitchRulerRef.current.scrollTop = event.currentTarget.scrollTop;
        }}
      >
        <div
          className="roll-canvas"
          style={{ width: TOTAL_TICKS * CELL_WIDTH, height: VISIBLE_PITCHES.length * ROW_HEIGHT }}
          onClick={() => selectNote(null)}
          onDoubleClick={addAtPointer}
        >
          {track.notes.map((note) => (
            <NoteBlock key={note.id} note={note} selected={selectedNoteIds.includes(note.id)} />
          ))}
        </div>
      </div>
    </div>
  );
}
