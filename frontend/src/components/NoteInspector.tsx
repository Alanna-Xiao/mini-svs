import { ArrowDown, ArrowUp, Trash2 } from "lucide-react";

import { activeTrack, selectedNote, useProjectStore } from "../state/projectStore";

export function NoteInspector() {
  const note = useProjectStore(selectedNote);
  const track = useProjectStore(activeTrack);
  const selectedCount = useProjectStore((state) => state.selectedNoteIds.length);
  const setTrackName = useProjectStore((state) => state.setTrackName);
  const moveTrack = useProjectStore((state) => state.moveTrack);
  const updateNote = useProjectStore((state) => state.updateNote);
  const deleteSelectedNotes = useProjectStore((state) => state.deleteSelectedNotes);
  const trackIndex = useProjectStore((state) =>
    state.project.tracks.findIndex((item) => item.id === state.activeTrackId),
  );
  const trackCount = useProjectStore((state) => state.project.tracks.length);

  return (
    <aside className="note-inspector" aria-label="Track and note inspector">
      <div className="panel-heading">Inspector</div>
      <div className="track-inspector">
        <div className="track-name-row">
          <label>
            Track name
            <input
              maxLength={64}
              value={track.name}
              onChange={(event) => setTrackName(track.id, event.target.value)}
              onBlur={(event) => {
                if (!event.target.value.trim()) {
                  setTrackName(track.id, track.type === "vocal" ? "Vocal" : "Instrument");
                }
              }}
            />
          </label>
          <div className="track-order" aria-label="Track order">
            <button
              title="Move track up"
              disabled={trackIndex <= 0}
              onClick={() => moveTrack(track.id, -1)}
            >
              <ArrowUp size={14} aria-hidden="true" />
            </button>
            <button
              title="Move track down"
              disabled={trackIndex < 0 || trackIndex >= trackCount - 1}
              onClick={() => moveTrack(track.id, 1)}
            >
              <ArrowDown size={14} aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
      {selectedCount > 1 ? (
        <div className="bulk-selection">
          <strong>{selectedCount} notes selected</strong>
          <button className="danger-button" onClick={deleteSelectedNotes}>
            <Trash2 size={15} aria-hidden="true" /> Delete {selectedCount} Notes
          </button>
        </div>
      ) : !note ? (
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
          <button className="danger-button" onClick={deleteSelectedNotes}>
            <Trash2 size={15} aria-hidden="true" /> Delete
          </button>
        </div>
      )}
    </aside>
  );
}
