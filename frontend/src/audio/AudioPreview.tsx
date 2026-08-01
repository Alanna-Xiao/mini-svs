import { useEffect, useRef } from "react";
import WaveSurfer from "wavesurfer.js";

export function AudioPreview({ url }: { url: string | null }) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!url || !container.current) return;
    const wave = WaveSurfer.create({
      container: container.current,
      url,
      height: 34,
      waveColor: "#78828d",
      progressColor: "#10a8a0",
      cursorColor: "#e6a23c",
    });
    return () => wave.destroy();
  }, [url]);

  return <div className="audio-preview" ref={container} aria-label="Rendered audio waveform" />;
}
