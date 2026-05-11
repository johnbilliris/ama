/**
 * Spec-038 Measurement Method tab — live fetch (T-AMD-15).
 * Fetches from GET /api/v1/evidence/measurement-method on mount.
 */
"use client";
import { useEffect, useState } from "react";

export default function MeasurementTab() {
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/v1/evidence/measurement-method?format=markdown")
      .then((r) => {
        if (!r.ok) { setError(`HTTP ${r.status}`); return null; }
        return r.json();
      })
      .then((d) => d && setContent(d.content ?? JSON.stringify(d)))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div data-testid="evidence-measurement-tab">
      {error && <p role="alert" className="text-red-600">Failed to load: {error}</p>}
      {!content && !error && <p>Loading Measurement Method…</p>}
      {content && <pre className="whitespace-pre-wrap text-sm">{content}</pre>}
    </div>
  );
}
