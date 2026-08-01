import { Trash2 } from "lucide-react";

import { selectedNote, useProjectStore } from "../state/projectStore";

export function NoteInspector() {
  const note = useProjectStore(selectedNote);
  const updateNote = useProjectStore((state) => state.updateNote);
  const deleteSelectedNote = useProjectStore((state) => state.deleteSelectedNote);

  return (
    <aside className="note-inspector" aria-label="Note inspector">
      <div className="panel-heading">Note</div>
      {!note ? (
        <div className="empty-inspector">No selection</div>
      ) : (
        <div className="inspector-fields">
          <label>
            Pitch
            <input value={note.pitch} onChange={(event) => updateNote(note.id, { pitch: event.target.value })} />
          </label>
          <label>
            Start
            <input
              type="number"
              min="0"
              value={note.start}
              onChange={(event) => updateNote(note.id, { start: Math.max(0, Number(event.target.value)) })}
            />
          </label>
          <label>
            Length
            <input
              type="number"
              min="1"
              value={note.duration}
              onChange={(event) => updateNote(note.id, { duration: Math.max(1, Number(event.target.value)) })}
            />
          </label>
          {note.type === "vocal" ? (
            <label>
              Lyric
              <input value={note.lyric} onChange={(event) => updateNote(note.id, { lyric: event.target.value })} />
            </label>
          ) : (
            <label>
              Velocity
              <input
                type="number"
                min="1"
                max="127"
                value={note.velocity}
                onChange={(event) =>
                  updateNote(note.id, { velocity: Math.min(127, Math.max(1, Number(event.target.value))) })
                }
              />
            </label>
          )}
          <button className="danger-button" onClick={deleteSelectedNote}>
            <Trash2 size={15} aria-hidden="true" /> Delete
          </button>
        </div>
      )}
    </aside>
  );
}
