"use client";

import { useId, useState, type CSSProperties, type ReactNode } from "react";

interface TooltipProps {
  /** Content to show inside the tooltip popover */
  content: ReactNode;
  /** Trigger element the user hovers / focuses */
  children: ReactNode;
  /** Tooltip placement relative to the trigger */
  side?: "top" | "bottom";
  /** Width of the tooltip popover in pixels. Defaults to 280. */
  widthPx?: number;
}

const wrapperStyle: CSSProperties = {
  position: "relative",
  display: "inline-flex",
  alignItems: "center",
};

const triggerStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  outline: "none",
  cursor: "help",
  borderRadius: 2,
};

/**
 * Accessible hover/focus tooltip.
 *
 * Wraps a focusable trigger and reveals a popover (`role="tooltip"`)
 * on mouse enter or keyboard focus. Associated to the trigger via
 * `aria-describedby` so assistive tech announces the description when
 * the trigger receives focus. Inline styles are used so the component
 * works regardless of whether Tailwind utility classes are present.
 */
export function Tooltip({
  content,
  children,
  side = "top",
  widthPx = 280,
}: TooltipProps) {
  const [open, setOpen] = useState(false);
  const id = useId();

  const popoverStyle: CSSProperties = {
    position: "absolute",
    left: "50%",
    transform: "translateX(-50%)",
    [side === "top" ? "bottom" : "top"]: "calc(100% + 4px)",
    width: widthPx,
    maxWidth: "min(90vw, 360px)",
    backgroundColor: "#111827",
    color: "#fff",
    padding: "8px 10px",
    borderRadius: 6,
    fontSize: 12,
    lineHeight: 1.4,
    textAlign: "left",
    whiteSpace: "normal",
    boxShadow: "0 4px 12px rgba(0,0,0,0.25)",
    pointerEvents: "none",
    zIndex: 50,
  };

  return (
    <span style={wrapperStyle}>
      <span
        tabIndex={0}
        aria-describedby={open ? id : undefined}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={(e) => {
          if (e.key === "Escape") setOpen(false);
        }}
        style={triggerStyle}
      >
        {children}
      </span>
      {open && (
        <span id={id} role="tooltip" style={popoverStyle}>
          {content}
        </span>
      )}
    </span>
  );
}

