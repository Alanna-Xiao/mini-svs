import { Mic2, Piano } from "lucide-react";

import { useProjectStore } from "../state/projectStore";

export function TrackList() {
  const tracks = useProjectStore((state) => state.project.tracks);
  const activeTrackId = useProjectStore((state) => state.activeTrackId);
  const setActiveTrack = useProjectStore((state) => state.setActiveTrack);

  return (
    <aside className="track-list" aria-label="Tracks">
      <div className="panel-heading">Tracks</div>
      {tracks.map((track) => {
        const Icon = track.type === "vocal" ? Mic2 : Piano;
        const resource = track.type === "vocal" ? track.voicebankId : track.instrumentId;
        return (
          <button
            key={track.id}
            className={track.id === activeTrackId ? "track-row active" : "track-row"}
            onClick={() => setActiveTrack(track.id)}
          >
            <Icon size={16} aria-hidden="true" />
            <span>
              <strong>{track.name}</strong>
              <small>{resource}</small>
            </span>
          </button>
        );
      })}
    </aside>
  );
}
