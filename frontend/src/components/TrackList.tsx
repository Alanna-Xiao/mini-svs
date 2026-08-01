import { Mic2, Music2, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { listInstruments } from "../api/client";
import { useProjectStore } from "../state/projectStore";
import type { InstrumentSummary } from "../types/project";

export function TrackList() {
  const tracks = useProjectStore((state) => state.project.tracks);
  const activeTrackId = useProjectStore((state) => state.activeTrackId);
  const setActiveTrack = useProjectStore((state) => state.setActiveTrack);
  const setTrackInstrument = useProjectStore((state) => state.setTrackInstrument);
  const addInstrumentTrack = useProjectStore((state) => state.addInstrumentTrack);
  const deleteInstrumentTrack = useProjectStore((state) => state.deleteInstrumentTrack);
  const [instruments, setInstruments] = useState<InstrumentSummary[]>([]);

  useEffect(() => {
    void listInstruments().then(setInstruments).catch(() => setInstruments([]));
  }, []);

  return (
    <aside className="track-list" aria-label="Tracks">
      <div className="panel-heading track-heading">
        <span>Tracks</span>
        <button
          className="track-add"
          title="Add instrument track"
          disabled={tracks.length >= 16}
          onClick={() => {
            const preset = instruments[0] ?? {
              id: "musescore_general",
              name: "Acoustic Grand Piano",
              format: "sf3" as const,
            };
            addInstrumentTrack(preset.id, preset.name);
          }}
        >
          <Plus size={14} aria-hidden="true" />
        </button>
      </div>
      {tracks.map((track) => {
        const Icon = track.type === "vocal" ? Mic2 : Music2;
        const resource = track.type === "vocal" ? track.voicebankId : track.instrumentId;
        return (
          <div
            key={track.id}
            className={track.id === activeTrackId ? "track-row active" : "track-row"}
          >
            <button className="track-main" onClick={() => setActiveTrack(track.id)}>
              <Icon size={16} aria-hidden="true" />
              <span>
                <strong>{track.name}</strong>
                <small>{resource}</small>
              </span>
            </button>
            {track.type === "instrument" ? (
              <button
                className="track-delete"
                title={`Delete ${track.name} track`}
                onClick={() => deleteInstrumentTrack(track.id)}
              >
                <Trash2 size={13} aria-hidden="true" />
              </button>
            ) : null}
            {track.type === "instrument" && instruments.length > 0 ? (
              <select
                aria-label="Instrument sound"
                value={track.instrumentId}
                onChange={(event) => {
                  const selected = instruments.find(
                    (instrument) => instrument.id === event.target.value,
                  );
                  if (selected) setTrackInstrument(track.id, selected.id, selected.name);
                }}
              >
                {instruments.map((instrument) => (
                  <option key={instrument.id} value={instrument.id}>
                    {instrument.name}
                  </option>
                ))}
              </select>
            ) : null}
          </div>
        );
      })}
    </aside>
  );
}
