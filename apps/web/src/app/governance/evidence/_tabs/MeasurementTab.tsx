"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getMeasurementMethod } from "../../../../lib/api/evidence";

export default function MeasurementTab() {
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback((signal?: AbortSignal) => {
    setLoading(true);
    setError("");
    void getMeasurementMethod(signal)
      .then(setContent)
      .catch((reason: unknown) => {
        if ((reason as Error).name !== "AbortError") setError(String(reason));
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const sections = useMemo(
    () => content.split("\n").filter((line) => line.startsWith("## ")),
    [content],
  );

  return (
    <div data-testid="evidence-measurement-tab">
      {loading ? <p role="status">Loading measurement method…</p> : null}
      {error ? (
        <div role="alert">
          <p>Failed to load the measurement method: {error}</p>
          <button type="button" onClick={() => load()}>Retry</button>
        </div>
      ) : null}
      {content ? (
        <div className="grid gap-4 lg:grid-cols-[16rem_1fr]">
          <nav aria-label="Measurement method contents">
            <ul>
              {sections.map((section) => (
                <li key={section}>{section.replace(/^## /, "")}</li>
              ))}
            </ul>
          </nav>
          <article className="prose whitespace-pre-wrap">{content}</article>
        </div>
      ) : null}
    </div>
  );
}
