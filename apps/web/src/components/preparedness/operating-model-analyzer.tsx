"use client";

import { useEffect, useDeferredValue, useState } from "react";

import type { PreparednessFramework } from "../../lib/api/frameworks";
import type { PreparednessOrganisation } from "../../lib/api/organisations";
import { replayPreparednessScenario, type ScenarioRunPayload } from "../../lib/api/scenarios";

interface OperatingModelAnalyzerProps {
  organisations: PreparednessOrganisation[];
  frameworks: PreparednessFramework[];
  selectedJurisdictionIds: string[];
  isLoading: boolean;
  replayStale: boolean;
  onReplayComplete: () => void;
}

const DEFAULT_SCENARIO: ScenarioRunPayload = {
  scenario_run_id: "scenario-pending",
  scenario_name: "Preparedness rehearsal pending",
  scenario_type: "flood",
  jurisdiction_ids: [],
  organisation_ids: [],
  framework_ids: [],
  coordination_gap_summary: [],
  generated_findings: ["Run a rehearsal to generate coordination findings."],
};

export function OperatingModelAnalyzer({
  organisations,
  frameworks,
  selectedJurisdictionIds,
  isLoading,
  replayStale,
  onReplayComplete,
}: OperatingModelAnalyzerProps) {
  const [scenarioType, setScenarioType] = useState("flood");
  const [scenarioRun, setScenarioRun] = useState<ScenarioRunPayload>(DEFAULT_SCENARIO);
  const [replayError, setReplayError] = useState<string | null>(null);
  const [replaying, setReplaying] = useState(false);
  const deferredScenarioRun = useDeferredValue(scenarioRun);

  useEffect(() => {
    if (replayStale) {
      setScenarioRun(DEFAULT_SCENARIO);
    }
  }, [replayStale]);

  const noJurisdictions = selectedJurisdictionIds.length === 0;

  function handleReplay() {
    setReplayError(null);
    setReplaying(true);
    replayPreparednessScenario("Preparedness rehearsal", scenarioType, selectedJurisdictionIds)
      .then((result) => {
        setScenarioRun(result);
        onReplayComplete();
      })
      .catch((err: Error) => setReplayError(err.message || "Rehearsal replay failed. The API may be temporarily unavailable."))
      .finally(() => setReplaying(false));
  }

  return (
    <section className="preparedness-shell">
      <header className="preparedness-header">
        <p className="preparedness-kicker">Preparedness analysis</p>
        <h1 className="preparedness-title">Agency operating model analyser</h1>
        <p className="preparedness-copy">
          Review jurisdiction coverage, assigned operating frameworks, and likely coordination gaps before a live event.
        </p>
      </header>

      {noJurisdictions && (
        <div className="preparedness-empty-state" role="status">
          <p>Select one or more jurisdictions above to view the organisation and framework catalogs.</p>
        </div>
      )}

      {!noJurisdictions && (
        <div className="preparedness-columns">
          <article className="preparedness-panel">
            <h2 className="preparedness-panel-title">Organisation catalog</h2>
            {isLoading ? (
              <p className="preparedness-loading">Loading organisations…</p>
            ) : organisations.length === 0 ? (
              <p className="preparedness-meta">No organisations found for the selected jurisdictions.</p>
            ) : (
              <ul className="preparedness-list">
                {organisations.map((organisation) => (
                  <li key={organisation.organisation_id} className="preparedness-list-item">
                    <strong>{organisation.name}</strong>
                    <div className="preparedness-meta">
                      {organisation.category} · {organisation.operating_role} · {organisation.authority_level}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article className="preparedness-panel">
            <h2 className="preparedness-panel-title">Framework catalog</h2>
            {isLoading ? (
              <p className="preparedness-loading">Loading frameworks…</p>
            ) : frameworks.length === 0 ? (
              <p className="preparedness-meta">No frameworks found for the selected jurisdictions.</p>
            ) : (
              <ul className="preparedness-list">
                {frameworks.map((framework) => (
                  <li key={framework.framework_id} className="preparedness-list-item">
                    <strong>{framework.name}</strong>
                    <div className="preparedness-meta">
                      {framework.framework_type} · {framework.span_of_control_guidance}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </div>
      )}

      <section className="preparedness-replay-panel">
        <div className="preparedness-replay-controls">
          <label className="preparedness-field">
            <span>Scenario type</span>
            <select
              className="preparedness-select"
              value={scenarioType}
              onChange={(event: { target: { value: string } }) => setScenarioType(event.target.value)}
            >
              <option value="flood">Flood</option>
              <option value="bushfire">Bushfire</option>
              <option value="cyclone">Cyclone</option>
            </select>
          </label>
          <button
            type="button"
            className="preparedness-button"
            onClick={handleReplay}
            disabled={replaying || noJurisdictions}
            title={noJurisdictions ? "Select at least one jurisdiction to run a rehearsal replay" : undefined}
          >
            {replaying ? "Running…" : "Run rehearsal replay"}
          </button>
          {noJurisdictions && (
            <span className="preparedness-meta">Select at least one jurisdiction to run a rehearsal replay.</span>
          )}
        </div>

        {replayStale && (
          <div className="preparedness-stale-notice" role="status">
            <p>Replay results were generated for different jurisdictions. Run a new replay for updated results.</p>
          </div>
        )}

        {replayError && (
          <div className="preparedness-error" role="alert">
            <p><strong>Rehearsal replay failed:</strong> {replayError}</p>
            <button type="button" className="preparedness-button" onClick={handleReplay} disabled={replaying || noJurisdictions}>
              Retry
            </button>
          </div>
        )}

        <div className="preparedness-columns">
          <article className="preparedness-panel preparedness-dark-panel">
            <h2 className="preparedness-panel-title">Findings</h2>
            <ul className="preparedness-list">
              {deferredScenarioRun.generated_findings.map((finding) => (
                <li key={finding} className="preparedness-list-item preparedness-dark-item">
                  {finding}
                </li>
              ))}
            </ul>
          </article>

          <article className="preparedness-panel">
            <h2 className="preparedness-panel-title">Coordination gaps</h2>
            <ul className="preparedness-list">
              {deferredScenarioRun.coordination_gap_summary.length === 0 ? (
                <li className="preparedness-list-item">No blocking gaps detected for the selected rehearsal.</li>
              ) : (
                deferredScenarioRun.coordination_gap_summary.map((gap) => (
                  <li key={gap} className="preparedness-list-item">
                    {gap}
                  </li>
                ))
              )}
            </ul>
          </article>
        </div>
      </section>
    </section>
  );
}
