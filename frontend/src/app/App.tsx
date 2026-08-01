import { AudioWaveform, Play, Square } from "lucide-react";
import { useState } from "react";

import { renderProject } from "../api/client";
import { AudioPreview } from "../audio/AudioPreview";
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
  const [status, setStatus] = useState("Ready");
  const [outputUrl, setOutputUrl] = useState<string | null>(null);

  const handleRender = async () => {
    setStatus("Rendering...");
    try {
      const result = await renderProject(project);
      setOutputUrl(`/api${result.outputUrl}`);
      setStatus(`Rendered ${result.metadata.durationSeconds.toFixed(2)} s`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Render failed");
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">mini-svs <span>0.1</span></div>
        <div className="transport" aria-label="Transport">
          <button className="icon-button" title="Play preview" disabled={!outputUrl}>
            <Play size={17} fill="currentColor" aria-hidden="true" />
          </button>
          <button className="icon-button" title="Stop preview" disabled={!outputUrl}>
            <Square size={15} fill="currentColor" aria-hidden="true" />
          </button>
          <button className="command-button" onClick={handleRender}>
            <AudioWaveform size={17} aria-hidden="true" /> Render
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
        <AudioPreview url={outputUrl} />
        <span>{project.sampleRate / 1000} kHz</span>
      </footer>
    </div>
  );
}
