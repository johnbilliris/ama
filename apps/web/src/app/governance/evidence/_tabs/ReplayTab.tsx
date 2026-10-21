"use client";

import type { DeltaScorecard } from "@ama/domain";
import { useCallback, useEffect, useState } from "react";
import {
  EvidenceApiError,
  getLatestScorecard,
  runReplay,
} from "../../../../lib/api/evidence";

const SCENARIOS = [
  "bushfire",
  "flood",
  "cyclone",
  "urban_fire",
  "mass_casualty",
  "hazmat",
  "marine_sar",
] as const;

interface ReplayTabProps {
  onScorecardSelected?: (scorecardId: string) => void;
}

export default function ReplayTab({ onScorecardSelected }: ReplayTabProps) {
  const [scenarioId, setScenarioId] = useState<string>("bushfire");
  const [seed, setSeed] = useState("exercise-seed");
  const [repetitions, setRepetitions] = useState(2);
  const [allowDegradedMode, setAllowDegradedMode] = useState(true);
  const [scorecard, setScorecard] = useState<DeltaScorecard | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const loadLatest = useCallback(
    (signal?: AbortSignal) => {
      setLoading(true);
      setError("");
      void getLatestScorecard(scenarioId, signal)
        .then((latest) => {
          setScorecard(latest);
          if (latest) onScorecardSelected?.(latest.id);
        })
        .catch((reason: unknown) => {
          if ((reason as Error).name === "AbortError") return;
          if (reason instanceof EvidenceApiError && reason.status === 404) {
            setScorecard(null);
            return;
          }
          setError(String(reason));
        })
        .finally(() => setLoading(false));
    },
    [onScorecardSelected, scenarioId],
  );

  useEffect(() => {
    const controller = new AbortController();
    loadLatest(controller.signal);
    return () => controller.abort();
  }, [loadLatest]);

  async function submitReplay() {
    setRunning(true);
    setError("");
    try {
      const created = await runReplay(scenarioId, {
        seed,
        run_pair_id: crypto.randomUUID(),
        repetitions,
        allow_degraded_mode: allowDegradedMode,
      });
      setScorecard(created);
      onScorecardSelected?.(created.id);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div data-testid="evidence-replay-tab">
      <form
        className="mb-4 grid gap-3 md:grid-cols-2"
        onSubmit={(event) => {
          event.preventDefault();
          void submitReplay();
        }}
      >
        <label>
          Scenario{" "}
          <select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>
            {SCENARIOS.map((scenario) => (
              <option key={scenario} value={scenario}>{scenario.replaceAll("_", " ")}</option>
            ))}
          </select>
        </label>
        <label>
          Seed{" "}
          <input value={seed} onChange={(event) => setSeed(event.target.value)} required />
        </label>
        <label>
          Repetitions{" "}
          <input
            type="number"
            min={1}
            max={100}
            value={repetitions}
            onChange={(event) => setRepetitions(Number(event.target.value))}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={allowDegradedMode}
            onChange={(event) => setAllowDegradedMode(event.target.checked)}
          />{" "}
          Permit explicit no-signal rows
        </label>
        <button type="submit" disabled={running}>{running ? "Running…" : "Run replay"}</button>
      </form>
      {loading ? <p role="status">Loading latest persisted scorecard…</p> : null}
      {error ? (
        <div role="alert">
          <p>Replay failed: {error}</p>
          <button type="button" onClick={() => loadLatest()}>Retry latest</button>
        </div>
      ) : null}
      {!loading && !error && !scorecard ? (
        <p>No persisted scorecard exists for this scenario. Run a replay to create one.</p>
      ) : null}
      {scorecard ? (
        <div>
          <p>
            Scorecard <code>{scorecard.id}</code> · scenario version{" "}
            {scorecard.scenario_version ?? "unavailable"}
          </p>
          {scorecard.reduced_fidelity ? <span role="status">reduced-fidelity</span> : null}
          {scorecard.kpi_deltas.some((delta) => delta.small_sample) ? (
            <span role="status" className="ml-2">small-sample</span>
          ) : null}
          <table aria-label="Replay delta scorecard">
            <thead>
              <tr>
                <th>KPI</th>
                <th>Baseline</th>
                <th>AMA-assisted</th>
                <th>Absolute delta</th>
                <th>Percent delta</th>
                <th>95% band</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {scorecard.kpi_deltas.map((delta) => (
                <tr key={delta.kpi_id}>
                  <td>{delta.kpi_id}</td>
                  <td>{delta.baseline_value ?? "No signal"}</td>
                  <td>{delta.ama_assisted_value ?? "No signal"}</td>
                  <td>{delta.absolute_delta ?? "—"} {delta.delta_unit}</td>
                  <td>{delta.percent_delta ?? "—"}</td>
                  <td>
                    {delta.confidence_band_low == null
                      ? "Unavailable"
                      : `${delta.confidence_band_low}–${delta.confidence_band_high}`}
                  </td>
                  <td>{delta.meets_target ? "Met" : "Not met"}</td>
                  <td>{delta.measurement_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {scorecard.determinism?.diverged ? (
            <p role="alert">Divergence detected across same-seed KPI deltas.</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
