import { AudioWaveform, Layers3, Play, Square } from "lucide-react";
import { useRef, useState } from "react";

import { renderProject } from "../api/client";
import { AudioPreview, type AudioPreviewHandle } from "../audio/AudioPreview";
import { NoteInspector } from "../components/NoteInspector";
import { TrackList } from "../components/TrackList";
import { PianoRoll } from "../editor/PianoRoll";
import { useProjectStore } from "../state/projectStore";
import type { GridUnit } from "../types/project";

const GRID_UNITS: GridUnit[] = ["1/4", "1/8", "1/16", "1/32"];

export function App() {
  const project = useProjectStore((state) => state.project);
  const setBpm = useProjectStore((state) => state.setBpm);
  const setGrid = useProjectStore((state) => state.setGrid);
  const activeTrackId = useProjectStore((state) => state.activeTrackId);
  const [status, setStatus] = useState("Ready");
  const [outputUrl, setOutputUrl] = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState(false);
  const audioPreview = useRef<AudioPreviewHandle>(null);

  const handleRender = async (trackIds?: string[]) => {
    const isMix = trackIds === undefined;
    setStatus(isMix ? "Mixing..." : "Rendering...");
    setOutputUrl(null);
    setIsRendering(true);
    try {
      const result = await renderProject(project, trackIds);
      setOutputUrl(`/api${result.outputUrl}`);
      setStatus(`${isMix ? "Mixed" : "Rendered"} ${result.metadata.durationSeconds.toFixed(2)} s`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Render failed");
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">mini-svs <span>0.1</span></div>
        <div className="transport" aria-label="Transport">
          <button
            className="icon-button"
            title="Play or pause preview"
            disabled={!outputUrl}
            onClick={() => audioPreview.current?.playPause()}
          >
            <Play size={17} fill="currentColor" aria-hidden="true" />
          </button>
          <button
            className="icon-button"
            title="Stop preview"
            disabled={!outputUrl}
            onClick={() => audioPreview.current?.stop()}
          >
            <Square size={15} fill="currentColor" aria-hidden="true" />
          </button>
          <button className="command-button" disabled={isRendering} onClick={() => handleRender([activeTrackId])}>
            <AudioWaveform size={17} aria-hidden="true" /> Render
          </button>
          <button className="command-button mix-button" disabled={isRendering} onClick={() => handleRender()}>
            <Layers3 size={17} aria-hidden="true" /> Mix
          </button>
        </div>
        <div className="project-controls">
          <label className="bpm-control">
            BPM
            <input type="number" min="20" max="400" value={project.bpm} onChange={(event) => setBpm(Number(event.target.value))} />
          </label>
          <div className="segmented" aria-label="Grid resolution">
            {GRID_UNITS.map((unit) => (
              <button key={unit} className={project.grid === unit ? "active" : ""} onClick={() => setGrid(unit)}>
                {unit}
              </button>
            ))}
          </div>
        </div>
      </header>
      <main className="workspace">
        <TrackList />
        <section className="editor-area" aria-label="Piano roll editor">
          <PianoRoll />
        </section>
        <NoteInspector />
      </main>
      <footer className="statusbar">
        <span>{status}</span>
        <AudioPreview ref={audioPreview} url={outputUrl} />
        <span>{project.sampleRate / 1000} kHz</span>
      </footer>
    </div>
  );
}
