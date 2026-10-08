"use client";

import type { CausalChain } from "@ama/domain";
import { useCallback, useEffect, useState } from "react";
import { getCausalChain } from "../../../../lib/api/evidence";

const CAPABILITIES = [
  ["communication-agent", "Communication Agent"],
  ["evacuation-agent", "Evacuation Agent"],
  ["monitoring-agent", "Monitoring Agent"],
  ["resource-allocation-agent", "Resource Allocation Agent"],
  ["risk-assessment-agent", "Risk Assessment Agent"],
  ["foundry-rag-client", "Foundry RAG Client"],
  ["telemetry-injection-agent", "Telemetry-Injection Agent"],
] as const;

export default function ImpactTab() {
  const [capabilityId, setCapabilityId] = useState(CAPABILITIES[0][0]);
  const [chain, setChain] = useState<CausalChain | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    (signal?: AbortSignal) => {
      setLoading(true);
      setError("");
      void getCausalChain(capabilityId, signal)
        .then(setChain)
        .catch((reason: unknown) => {
          if ((reason as Error).name !== "AbortError") setError(String(reason));
        })
        .finally(() => setLoading(false));
    },
    [capabilityId],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  return (
    <div data-testid="evidence-impact-tab">
      <label>
        Capability{" "}
        <select
          value={capabilityId}
          onChange={(event) => setCapabilityId(event.target.value as typeof capabilityId)}
        >
          {CAPABILITIES.map(([id, label]) => (
            <option key={id} value={id}>{label}</option>
          ))}
        </select>
      </label>
      {loading ? <p role="status">Loading impact chain…</p> : null}
      {error ? (
        <div role="alert">
          <p>Failed to load the impact chain: {error}</p>
          <button type="button" onClick={() => load()}>Retry</button>
        </div>
      ) : null}
      {chain ? (
        <article>
          <h3>{chain.capability_name}</h3>
          <p>{chain.claim}</p>
          <p>
            Magnitude:{" "}
            {chain.magnitude_status === "hypothesis"
              ? "Hypothesis — no numeric effect claimed"
              : `${chain.expected_magnitude_value} ${chain.expected_magnitude_unit}`}
          </p>
          <p>
            Source: {chain.originating_spec_path} · {chain.originating_requirement}
          </p>
          <h4>Assumptions</h4>
          <ul>
            {chain.assumptions.map((assumption) => (
              <li key={assumption.id}>
                <strong>{assumption.review_state}</strong>: {assumption.text}
                <br />
                Test: {assumption.validation_method}
              </li>
            ))}
          </ul>
          {chain.assumptions.some((assumption) => !assumption.resolved) ? (
            <span role="status">unresolved assumptions</span>
          ) : null}
          <h4>Threats to validity</h4>
          <ul>
            {chain.threats_to_validity.map((threat) => (
              <li key={threat.text}>
                {threat.severity}: {threat.text} Mitigation: {threat.mitigation}
              </li>
            ))}
          </ul>
        </article>
      ) : null}
    </div>
  );
}
