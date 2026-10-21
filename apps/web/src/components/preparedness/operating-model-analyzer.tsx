"use client";

import { useEffect, useDeferredValue, useMemo, useState } from "react";

import type { JurisdictionSummary } from "../../lib/api/jurisdictions";
import type { PreparednessFramework } from "../../lib/api/frameworks";
import type { PreparednessOrganisation } from "../../lib/api/organisations";
import { replayPreparednessScenario, type ScenarioRunPayload } from "../../lib/api/scenarios";
import { useI18n } from "../../lib/i18n/runtime";

function formatLabel(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

interface OperatingModelAnalyzerProps {
  jurisdictions: JurisdictionSummary[];
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
  jurisdictions,
  organisations,
  frameworks,
  selectedJurisdictionIds,
  isLoading,
  replayStale,
  onReplayComplete,
}: OperatingModelAnalyzerProps) {
  const { t } = useI18n();
  const [orgCatalogueOpen, setOrgCatalogueOpen] = useState(true);
  const [fwCatalogueOpen, setFwCatalogueOpen] = useState(true);
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

  const orgLookup = useMemo(
    () => new Map(organisations.map((o) => [o.organisation_id, o])),
    [organisations],
  );

  const fwLookup = useMemo(
    () => new Map(frameworks.map((f) => [f.framework_id, f])),
    [frameworks],
  );

  const jurLookup = useMemo(
    () => new Map(jurisdictions.map((j) => [j.jurisdiction_id, j])),
    [jurisdictions],
  );

  function handleReplay() {
    setReplayError(null);
    setReplaying(true);
    replayPreparednessScenario("Preparedness rehearsal", scenarioType, selectedJurisdictionIds)
      .then((result) => {
        setScenarioRun(result);
        onReplayComplete();
      })
      .catch((err: Error) => setReplayError(err.message || t("preparedness.replayFailed")))
      .finally(() => setReplaying(false));
  }

  return (
    <section className="preparedness-shell">
      {!noJurisdictions && (
        <div className="preparedness-columns">
          <article className="preparedness-panel">
            <button
              type="button"
              className="preparedness-panel-toggle"
              onClick={() => setOrgCatalogueOpen((v) => !v)}
              aria-expanded={orgCatalogueOpen}
            >
              <span className={`preparedness-panel-chevron ${orgCatalogueOpen ? "preparedness-panel-chevron--open" : ""}`} aria-hidden="true">▶</span>
              <h2 className="preparedness-panel-title">Organisation catalogue</h2>
            </button>
            {orgCatalogueOpen && (
              <>
                {isLoading ? (
                  <p className="preparedness-loading">Loading organisations…</p>
                ) : organisations.length === 0 ? (
                  <p className="preparedness-meta">No organisations found for the selected jurisdictions.</p>
                ) : (
                  <ul className="preparedness-list">
                    {organisations.map((org) => (
                      <li key={org.organisation_id} className="preparedness-list-item preparedness-org-card">
                        <div className="preparedness-org-header">
                          <strong>{org.abbreviation ? `${org.name} (${org.abbreviation})` : org.name}</strong>
                          {org.workforce_type && (
                            <span className={`preparedness-badge preparedness-badge--${org.workforce_type}`}>
                              {org.workforce_type}
                            </span>
                          )}
                        </div>
                        <div className="preparedness-meta">
                          {formatLabel(org.category)} · {formatLabel(org.operating_role)} · {formatLabel(org.authority_level)}
                        </div>
                        {org.aiims_functions.length > 0 && (
                          <div className="preparedness-tag-row">
                            {org.aiims_functions.map((fn) => (
                              <span key={fn} className="preparedness-tag preparedness-tag--aiims">{formatLabel(fn)}</span>
                            ))}
                          </div>
                        )}
                        {org.hazard_types.length > 0 && (
                          <div className="preparedness-tag-row">
                            {org.hazard_types.map((h) => (
                              <span key={h} className="preparedness-tag preparedness-tag--hazard">{formatLabel(h)}</span>
                            ))}
                          </div>
                        )}
                        {org.primary_capabilities.length > 0 && (
                          <div className="preparedness-tag-row">
                            {org.primary_capabilities.slice(0, 4).map((c) => (
                              <span key={c} className="preparedness-tag preparedness-tag--capability">{formatLabel(c)}</span>
                            ))}
                            {org.primary_capabilities.length > 4 && (
                              <span className="preparedness-tag preparedness-tag--more">+{org.primary_capabilities.length - 4}</span>
                            )}
                          </div>
                        )}
                        {org.lead_agency_for.length > 0 && (
                          <div className="preparedness-org-lead">
                            Lead agency for: {org.lead_agency_for.map(formatLabel).join(", ")}
                          </div>
                        )}
                        {org.mutual_aid_partner_ids.length > 0 && (
                          <div className="preparedness-org-partners">
                            Mutual aid: {org.mutual_aid_partner_ids.map((pid) => {
                              const partner = orgLookup.get(pid);
                              return partner ? (partner.abbreviation ?? partner.name) : pid;
                            }).join(", ")}
                          </div>
                        )}
                        {org.legislative_basis && (
                          <div className="preparedness-org-legislation">{org.legislative_basis}</div>
                        )}
                        {org.activation_triggers.length > 0 && (
                          <details className="preparedness-org-details">
                            <summary>Activation triggers ({org.activation_triggers.length})</summary>
                            <ul className="preparedness-org-triggers">
                              {org.activation_triggers.map((t) => (
                                <li key={t}>{t}</li>
                              ))}
                            </ul>
                          </details>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </article>

          <article className="preparedness-panel">
            <button
              type="button"
              className="preparedness-panel-toggle"
              onClick={() => setFwCatalogueOpen((v) => !v)}
              aria-expanded={fwCatalogueOpen}
            >
              <span className={`preparedness-panel-chevron ${fwCatalogueOpen ? "preparedness-panel-chevron--open" : ""}`} aria-hidden="true">▶</span>
              <h2 className="preparedness-panel-title">Framework catalogue</h2>
            </button>
            {fwCatalogueOpen && (
              <>
                {isLoading ? (
                  <p className="preparedness-loading">Loading frameworks…</p>
                ) : frameworks.length === 0 ? (
                  <p className="preparedness-meta">No frameworks found for the selected jurisdictions.</p>
                ) : (
                  <ul className="preparedness-list">
                    {frameworks.map((fw) => (
                      <li key={fw.framework_id} className="preparedness-list-item preparedness-fw-card">
                        <div className="preparedness-org-header">
                          <strong>{fw.abbreviation ? `${fw.name} (${fw.abbreviation})` : fw.name}</strong>
                          <span className={`preparedness-badge preparedness-badge--fw-${fw.framework_type}`}>
                            {formatLabel(fw.framework_type)}
                          </span>
                        </div>
                        {fw.description && (
                          <div className="preparedness-fw-description">{fw.description}</div>
                        )}
                        {fw.pprr_phases.length > 0 && (
                          <div className="preparedness-tag-row">
                            {fw.pprr_phases.map((p) => (
                              <span key={p} className="preparedness-tag preparedness-tag--pprr">{formatLabel(p)}</span>
                            ))}
                          </div>
                        )}
                        {fw.hazard_types.length > 0 ? (
                          <div className="preparedness-tag-row">
                            {fw.hazard_types.map((h) => (
                              <span key={h} className="preparedness-tag preparedness-tag--hazard">{formatLabel(h)}</span>
                            ))}
                          </div>
                        ) : (
                          <div className="preparedness-meta">All hazards</div>
                        )}
                        {fw.custodian_organisation_id && (
                          <div className="preparedness-meta">
                            Custodian: {(() => {
                              const custodian = orgLookup.get(fw.custodian_organisation_id!);
                              return custodian ? (custodian.abbreviation ?? custodian.name) : fw.custodian_organisation_id;
                            })()}
                          </div>
                        )}
                        {fw.legislative_basis && (
                          <div className="preparedness-org-legislation">{fw.legislative_basis}</div>
                        )}
                        {(fw.activation_triggers.length > 0 || fw.principles.length > 0 || fw.version) && (
                          <details className="preparedness-org-details">
                            <summary>Details</summary>
                            {fw.version && <div className="preparedness-meta">Version: {fw.version}</div>}
                            {fw.principles.length > 0 && (
                              <div className="preparedness-fw-principles">
                                <strong>Principles:</strong> {fw.principles.join(", ")}
                              </div>
                            )}
                            {fw.span_of_control_guidance && (
                              <div className="preparedness-fw-principles">
                                <strong>Span of control:</strong> {fw.span_of_control_guidance}
                              </div>
                            )}
                            {fw.activation_triggers.length > 0 && (
                              <>
                                <strong>Activation triggers:</strong>
                                <ul className="preparedness-org-triggers">
                                  {fw.activation_triggers.map((t) => (
                                    <li key={t}>{t}</li>
                                  ))}
                                </ul>
                              </>
                            )}
                            {fw.source_uri && (
                              <div className="preparedness-meta">
                                <a href={fw.source_uri} target="_blank" rel="noopener noreferrer">Source document ↗</a>
                              </div>
                            )}
                          </details>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </article>
        </div>
      )}

      <section className="preparedness-replay-panel">
        <div className="preparedness-replay-controls">
          <label className="preparedness-field">
            <span>{t("preparedness.scenarioType")}</span>
            <select
              className="preparedness-select"
              value={scenarioType}
              onChange={(event: { target: { value: string } }) => setScenarioType(event.target.value)}
            >
              <option value="flood">Flood</option>
              <option value="bushfire">Bushfire</option>
              <option value="cyclone">Cyclone</option>
              <option value="severe_storm">Severe storm</option>
            </select>
          </label>
          <button
            type="button"
            className="preparedness-button"
            onClick={handleReplay}
            disabled={replaying || noJurisdictions}
            title={noJurisdictions ? "Select at least one jurisdiction to run a rehearsal replay" : undefined}
          >
            {replaying ? t("preparedness.running") : t("preparedness.runReplay")}
          </button>
          {noJurisdictions && (
            <span className="preparedness-meta">{t("preparedness.selectJurisdiction")}</span>
          )}
        </div>

        {replayStale && (
          <div className="preparedness-stale-notice" role="status">
            <p>{t("preparedness.resultsStale")}</p>
          </div>
        )}

        {replayError && (
          <div className="preparedness-error" role="alert">
            <p><strong>{t("preparedness.replayFailed")}</strong> {replayError}</p>
            <button type="button" className="preparedness-button" onClick={handleReplay} disabled={replaying || noJurisdictions}>
              {t("common.retry")}
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
                <li className="preparedness-list-item">{t("preparedness.noGaps")}</li>
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

        <div className="preparedness-columns preparedness-replay-detail">
          <article className="preparedness-panel">
            <h2 className="preparedness-panel-title">
              Jurisdictions ({deferredScenarioRun.jurisdiction_ids.length})
            </h2>
            <ul className="preparedness-list">
              {deferredScenarioRun.jurisdiction_ids.map((jid) => {
                const jur = jurLookup.get(jid);
                return (
                  <li key={jid} className="preparedness-list-item">
                    <strong>{jur ? jur.name : jid}</strong>
                    {jur && <span className="preparedness-meta"> · {formatLabel(jur.level)}</span>}
                  </li>
                );
              })}
            </ul>
          </article>

          <article className="preparedness-panel">
            <h2 className="preparedness-panel-title">
              Organisations ({deferredScenarioRun.organisation_ids.length})
            </h2>
            {deferredScenarioRun.organisation_ids.length === 0 ? (
              <p className="preparedness-meta">No organisations matched.</p>
            ) : (
              <ul className="preparedness-list">
                {deferredScenarioRun.organisation_ids.map((oid) => {
                  const org = orgLookup.get(oid);
                  return (
                    <li key={oid} className="preparedness-list-item">
                      <strong>{org ? (org.abbreviation ? `${org.abbreviation} — ${org.name}` : org.name) : oid}</strong>
                      {org && (
                        <div className="preparedness-meta">
                          {formatLabel(org.category)} · {formatLabel(org.operating_role)}
                          {org.workforce_type && ` · ${formatLabel(org.workforce_type)}`}
                        </div>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </article>

          <article className="preparedness-panel">
            <h2 className="preparedness-panel-title">
              Frameworks ({deferredScenarioRun.framework_ids.length})
            </h2>
            {deferredScenarioRun.framework_ids.length === 0 ? (
              <p className="preparedness-meta">No frameworks matched.</p>
            ) : (
              <ul className="preparedness-list">
                {deferredScenarioRun.framework_ids.map((fid) => {
                  const fw = fwLookup.get(fid);
                  return (
                    <li key={fid} className="preparedness-list-item">
                      <strong>{fw ? (fw.abbreviation ? `${fw.abbreviation} — ${fw.name}` : fw.name) : fid}</strong>
                      {fw && (
                        <>
                          <div className="preparedness-meta">{formatLabel(fw.framework_type)}</div>
                          {fw.pprr_phases.length > 0 && (
                            <div className="preparedness-tag-row">
                              {fw.pprr_phases.map((p) => (
                                <span key={p} className="preparedness-tag preparedness-tag--pprr">{formatLabel(p)}</span>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </article>
        </div>
      </section>
    </section>
  );
}
