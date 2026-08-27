import { AudioWaveform, ChevronDown, Layers3 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

type RenderMenuProps = {
  disabled: boolean;
  onRenderActive: () => void;
  onRenderAll: () => void;
};

export function RenderMenu({ disabled, onRenderActive, onRenderAll }: RenderMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menu = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!menu.current?.contains(event.target as Node)) setIsOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };

    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [isOpen]);

  return (
    <div className="render-menu" ref={menu}>
      <div className="render-split">
        <button
          className="command-button render-primary"
          aria-label="Render"
          title="Render active track"
          disabled={disabled}
          onClick={() => {
            setIsOpen(false);
            onRenderActive();
          }}
        >
          <AudioWaveform size={17} aria-hidden="true" /> <span>Render</span>
        </button>
        <button
          className="command-button render-toggle"
          aria-label="Render options"
          title="Render options"
          aria-haspopup="menu"
          aria-expanded={isOpen}
          disabled={disabled}
          onClick={() => setIsOpen((current) => !current)}
        >
          <ChevronDown size={15} aria-hidden="true" />
        </button>
      </div>
      {isOpen ? (
        <div className="render-options" role="menu">
          <button
            role="menuitem"
            onClick={() => {
              setIsOpen(false);
              onRenderAll();
            }}
          >
            <Layers3 size={16} aria-hidden="true" />
            <span>
              <strong>Render all tracks</strong>
              <small>Preview the complete mix</small>
            </span>
          </button>
        </div>
      ) : null}
    </div>
  );
}
