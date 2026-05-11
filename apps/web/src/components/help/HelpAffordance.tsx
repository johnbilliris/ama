"use client";
/** spec-038 T-AA106 — global help affordance (?, Ctrl+/). */
import { useEffect, useState } from "react";
import { trackHelpEvent } from "@/lib/help/telemetry";

export function HelpAffordance({ surface }: { surface: string }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "/") {
        e.preventDefault();
        setOpen((o) => !o);
        trackHelpEvent({ name: "help.affordance.opened", surface });
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [surface]);
  return (
    <>
      <button
        type="button"
        aria-label="Open Help"
        aria-keyshortcuts="Control+/ Meta+/"
        className="rounded-full border border-gray-300 px-2 py-1 text-sm"
        onClick={() => {
          setOpen(true);
          trackHelpEvent({ name: "help.affordance.opened", surface });
        }}
      >
        ?
      </button>
      {open ? (
        <aside role="dialog" aria-label="Help" className="fixed right-0 top-0 h-full w-96 border-l bg-white p-4 shadow-lg">
          <button type="button" onClick={() => setOpen(false)} aria-label="Close Help">×</button>
          <p>Help for {surface}</p>
        </aside>
      ) : null}
    </>
  );
}
