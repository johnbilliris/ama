"use client";
/** spec-038 T-AA120 — first-fifteen-minutes tour overlay. */
import { useState } from "react";

export interface TourStep {
  title: string;
  body: string;
}

export function FirstFifteenMinutesTour({ steps, onComplete }: { steps: TourStep[]; onComplete?: () => void }) {
  const [i, setI] = useState(0);
  if (i >= steps.length) {
    onComplete?.();
    return null;
  }
  const s = steps[i];
  return (
    <div role="dialog" aria-label="Welcome tour" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="max-w-md rounded bg-white p-4">
        <h3 className="text-lg font-semibold">{s.title}</h3>
        <p className="mt-2 text-sm">{s.body}</p>
        <div className="mt-4 flex justify-between text-sm">
          <button type="button" onClick={() => onComplete?.()}>Skip</button>
          <button type="button" onClick={() => setI(i + 1)}>{i + 1 === steps.length ? "Finish" : "Next"}</button>
        </div>
      </div>
    </div>
  );
}
