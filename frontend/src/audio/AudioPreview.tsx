import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import WaveSurfer from "wavesurfer.js";

export interface AudioPreviewHandle {
  playPause: () => void;
  stop: () => void;
}

export const AudioPreview = forwardRef<AudioPreviewHandle, { url: string | null }>(function AudioPreview(
  { url },
  ref,
) {
  const container = useRef<HTMLDivElement>(null);
  const player = useRef<WaveSurfer | null>(null);

  useImperativeHandle(ref, () => ({
    playPause: () => {
      void player.current?.playPause();
    },
    stop: () => player.current?.stop(),
  }));

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
    player.current = wave;
    return () => {
      player.current = null;
      wave.destroy();
    };
  }, [url]);

  return <div className="audio-preview" ref={container} aria-label="Rendered audio waveform" />;
});
