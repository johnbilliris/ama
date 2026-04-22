"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getSimulation,
  pauseSimulation,
  resumeSimulation,
  archiveSimulation,
  type SimulationDetail,
  type SimulationClockResponse,
} from "@/lib/api/simulations";
import { SimulationBanner } from "@/components/simulation-banner";
import { SimulationChatPane } from "@/components/simulation-chat-pane";
import { SimulationMap, type ScenarioCard } from "@/components/simulation-map";
import { SimulationServerClock } from "@/components/simulation-server-clock";
import { SimulationWarpControls } from "@/components/simulation-warp-controls";

// ── PPRR phase derivation ──
function derivePPRRPhase(status: string, scenarioSeeded: boolean): string {
  if (status === "Archived") return "Recovery";
  if (status === "Paused") return "Preparedness";
  if (status === "Active" && scenarioSeeded) return "Response";
  return "Preparedness";
}

const PPRR_COLOURS: Record<string, string> = {
  Prevention: "#3b82f6",
  Preparedness: "#f59e0b",
  Response: "#dc2626",
  Recovery: "#22c55e",
};

// ── Exercise objectives ──
interface ExerciseObjective {
  id: string;
  text: string;
  done: boolean;
}

export default function SimulationDashboardPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const [tenant, setTenant] = useState<SimulationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scenarioCard, setScenarioCard] = useState<ScenarioCard | null>(null);
  const [eventLog, setEventLog] = useState<{ ts: string; text: string }[]>([]);
  const [objectives, setObjectives] = useState<ExerciseObjective[]>([]);
  const [newObj, setNewObj] = useState("");
  const [eventLogOpen, setEventLogOpen] = useState(true);
  const [objectivesOpen, setObjectivesOpen] = useState(true);
  const [currentWarpSpeed, setCurrentWarpSpeed] = useState<number>(1);

  const logEvent = useCallback((text: string) => {
    setEventLog((prev) => [...prev, { ts: new Date().toISOString(), text }]);
  }, []);

  useEffect(() => {
    if (!tenantId) return;
    getSimulation(tenantId)
      .then((data) => {
        setTenant(data);
        setCurrentWarpSpeed(data.current_warp_speed ?? data.warp_speed ?? 1);
        logEvent("Simulation dashboard loaded");
      })
      .catch((err) => setError(err.message));
  }, [tenantId, logEvent]);

  const onClockTick = useCallback(
    (c: SimulationClockResponse) => {
      setCurrentWarpSpeed(c.current_warp_speed);
      if (tenant && c.playback_status && c.playback_status !== tenant.playback_status) {
        setTenant((prev) =>
          prev ? { ...prev, playback_status: c.playback_status } : prev,
        );
      }
    },
    [tenant],
  );

  const pprr = derivePPRRPhase(tenant?.status ?? "", !!scenarioCard);

  if (error) {
    const isNotFound = /404/.test(error) || /not found/i.test(error);
    return (
      <div className="mx-auto max-w-2xl p-6">
        <h1 className="mb-2 text-2xl font-bold">
          {isNotFound ? "Simulation not found" : "Error loading simulation"}
        </h1>
        <p className="mb-4 text-sm text-gray-600">{error}</p>
        <Link href="/simulations" className="text-sm text-blue-600 hover:underline">
          ← Back to simulations list
        </Link>
      </div>
    );
  }
  if (!tenant) return <div className="p-6">Loading simulation dashboard...</div>;

  const signalPct = tenant.resource_limits.max_signals
    ? Math.round(
        (tenant.resource_consumption.signal_count / tenant.resource_limits.max_signals) * 100,
      )
    : 0;
  const recPct = tenant.resource_limits.max_recommendations
    ? Math.round(
        (tenant.resource_consumption.recommendation_count /
          tenant.resource_limits.max_recommendations) *
          100,
      )
    : 0;

  const handlePause = async () => {
    const result = await pauseSimulation(tenant.tenant_id);
    setTenant({
      ...tenant,
      status: "Paused",
      elapsed_seconds: result.elapsed_seconds,
      accumulated_sim_seconds: result.accumulated_sim_seconds,
      clock_paused: true,
    });
    logEvent("Simulation paused");
  };
  const handleResume = async () => {
    const result = await resumeSimulation(tenant.tenant_id);
    setTenant({
      ...tenant,
      status: "Active",
      elapsed_seconds: result.elapsed_seconds,
      accumulated_sim_seconds: result.accumulated_sim_seconds,
      clock_paused: false,
    });
    logEvent("Simulation resumed");
  };
  const handleStop = async () => {
    if (!window.confirm("Stop this simulation? This is terminal.")) return;
    const result = await archiveSimulation(tenant.tenant_id);
    setTenant({
      ...tenant,
      status: "Archiving",
      elapsed_seconds: result.elapsed_seconds,
    });
    logEvent("Simulation stopped (archiving)");
  };

  const addObjective = () => {
    const text = newObj.trim();
    if (!text) return;
    setObjectives((prev) => [...prev, { id: crypto.randomUUID(), text, done: false }]);
    setNewObj("");
  };

  const toggleObjective = (id: string) => {
    setObjectives((prev) => prev.map((o) => (o.id === id ? { ...o, done: !o.done } : o)));
  };

  const removeObjective = (id: string) => {
    setObjectives((prev) => prev.filter((o) => o.id !== id));
  };

  return (
    <div className="sim-dashboard-page">
      <SimulationBanner />
      <div className="sim-dashboard-wrap">
        <div className="sim-dashboard-layout">
          {/* ─────────────── LEFT: signals + tenant details ─────────────── */}
          <aside className="sim-side-panel">
            <section className="sim-panel-section">
              <header className="sim-panel-header">
                <h2>Simulation</h2>
                <div className="sim-header-badges">
                  <span
                    className="sim-pprr-badge"
                    style={{ background: PPRR_COLOURS[pprr] ?? "#6b7280" }}
                    title={`PPRR Phase: ${pprr}`}
                  >
                    {pprr}
                  </span>
                  <span className={`sim-status-pill sim-status-pill--${tenant.status}`}>
                    {tenant.status}
                  </span>
                </div>
              </header>

              {/* Server-owned simulation clock (polls /clock) */}
              <SimulationServerClock
                tenantId={tenant.tenant_id}
                onClock={onClockTick}
              />

              {/* Warp speed controls (US2 — live speed change) */}
              <SimulationWarpControls
                tenantId={tenant.tenant_id}
                currentWarpSpeed={currentWarpSpeed}
                disabled={!["Active", "Paused"].includes(tenant.status)}
                onChanged={(speed) => {
                  setCurrentWarpSpeed(speed);
                  logEvent(`Warp speed changed to ${speed}×`);
                }}
              />

              <dl className="sim-panel-meta">
                <div>
                  <dt>Scenario</dt>
                  <dd>{tenant.scenario_type}</dd>
                </div>
                <div>
                  <dt>Jurisdictions</dt>
                  <dd>{tenant.jurisdictions.join(", ") || "—"}</dd>
                </div>
                <div>
                  <dt>Created by</dt>
                  <dd>{tenant.created_by}</dd>
                </div>
                <div>
                  <dt>Created</dt>
                  <dd>{new Date(tenant.created_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Expires</dt>
                  <dd>{new Date(tenant.expires_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt>TTL</dt>
                  <dd>{tenant.ttl_hours}h</dd>
                </div>
                <div>
                  <dt>Throttle</dt>
                  <dd>
                    {tenant.throttle_mode} · {tenant.throttle_quota_pct}%
                  </dd>
                </div>
              </dl>
            </section>

            <section className="sim-panel-section">
              <header className="sim-panel-header">
                <h2>Signals & Resources</h2>
              </header>
              <div className="sim-meter-list">
                <Meter
                  label="Signals"
                  value={tenant.resource_consumption.signal_count}
                  limit={tenant.resource_limits.max_signals}
                  pct={signalPct}
                />
                <Meter
                  label="Recommendations"
                  value={tenant.resource_consumption.recommendation_count}
                  limit={tenant.resource_limits.max_recommendations}
                  pct={recPct}
                />
                <div className="sim-meter">
                  <div className="sim-meter-row">
                    <span>Storage</span>
                    <span className="sim-meter-value">
                      {(tenant.resource_consumption.storage_bytes / 1024).toFixed(1)} KB
                    </span>
                  </div>
                </div>
                <div className="sim-meter">
                  <div className="sim-meter-row">
                    <span>Participants</span>
                    <span className="sim-meter-value">{tenant.participants.length}</span>
                  </div>
                </div>
              </div>
            </section>

            <section className="sim-panel-section">
              <header className="sim-panel-header">
                <h2>Participants ({tenant.participants.length})</h2>
              </header>
              {tenant.participants.length === 0 ? (
                <p className="sim-panel-empty">No participants yet.</p>
              ) : (
                <ul className="sim-participant-list">
                  {tenant.participants.map((p) => (
                    <li key={p} title={p}>
                      {p}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="sim-panel-section">
              <header className="sim-panel-header">
                <h2>Controls</h2>
              </header>
              <div className="sim-control-buttons">
                <button
                  type="button"
                  className="sim-btn sim-btn--pause"
                  disabled={tenant.status !== "Active"}
                  onClick={handlePause}
                >
                  Pause
                </button>
                <button
                  type="button"
                  className="sim-btn sim-btn--resume"
                  disabled={tenant.status !== "Paused"}
                  onClick={handleResume}
                >
                  Resume
                </button>
                <button
                  type="button"
                  className="sim-btn sim-btn--stop"
                  disabled={!["Active", "Paused"].includes(tenant.status)}
                  onClick={handleStop}
                >
                  Stop
                </button>
              </div>
              <Link href="/simulations" className="sim-panel-backlink">
                ← Back to simulations
              </Link>
            </section>

            {/* ── Event Log ── */}
            <section className="sim-panel-section">
              <header
                className="sim-panel-header sim-collapsible-header"
                onClick={() => setEventLogOpen((v) => !v)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && setEventLogOpen((v) => !v)}
                aria-expanded={eventLogOpen}
              >
                <h2>Event Log ({eventLog.length})</h2>
                <span className="sim-collapse-icon">{eventLogOpen ? "▾" : "▸"}</span>
              </header>
              {eventLogOpen && (
                <div className="sim-event-log">
                  {eventLog.length === 0 ? (
                    <p className="sim-panel-empty">No events yet.</p>
                  ) : (
                    <ul className="sim-event-list">
                      {eventLog.map((ev, i) => (
                        <li key={i}>
                          <span className="sim-event-ts">
                            {new Date(ev.ts).toLocaleTimeString()}
                          </span>
                          <span className="sim-event-text">{ev.text}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </section>

            {/* ── Exercise Objectives ── */}
            <section className="sim-panel-section">
              <header
                className="sim-panel-header sim-collapsible-header"
                onClick={() => setObjectivesOpen((v) => !v)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && setObjectivesOpen((v) => !v)}
                aria-expanded={objectivesOpen}
              >
                <h2>
                  Exercise Objectives{" "}
                  {objectives.length > 0 && (
                    <span className="sim-obj-count">
                      {objectives.filter((o) => o.done).length}/{objectives.length}
                    </span>
                  )}
                </h2>
                <span className="sim-collapse-icon">{objectivesOpen ? "▾" : "▸"}</span>
              </header>
              {objectivesOpen && (
                <div className="sim-objectives">
                  {objectives.length === 0 && (
                    <p className="sim-panel-empty">Add learning goals for this exercise.</p>
                  )}
                  <ul className="sim-objectives-list">
                    {objectives.map((obj) => (
                      <li key={obj.id} className={obj.done ? "sim-obj-done" : ""}>
                        <label className="sim-obj-label">
                          <input
                            type="checkbox"
                            checked={obj.done}
                            onChange={() => toggleObjective(obj.id)}
                          />
                          <span>{obj.text}</span>
                        </label>
                        <button
                          type="button"
                          className="sim-obj-remove"
                          onClick={() => removeObjective(obj.id)}
                          title="Remove objective"
                          aria-label={`Remove objective: ${obj.text}`}
                        >
                          ×
                        </button>
                      </li>
                    ))}
                  </ul>
                  <div className="sim-obj-add">
                    <input
                      type="text"
                      value={newObj}
                      onChange={(e) => setNewObj(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addObjective()}
                      placeholder="Add objective…"
                      className="sim-obj-input"
                    />
                    <button
                      type="button"
                      onClick={addObjective}
                      className="sim-obj-add-btn"
                      disabled={!newObj.trim()}
                    >
                      +
                    </button>
                  </div>
                </div>
              )}
            </section>
          </aside>

          {/* ─────────────── CENTER: affected-area map ─────────────── */}
          <section className="sim-center-panel">
            <SimulationMap
              tenantId={tenant.tenant_id}
              scenarioType={tenant.scenario_type}
              jurisdictions={tenant.jurisdictions}
              status={tenant.status}
              scenarioCard={scenarioCard}
            />
          </section>

          {/* ─────────────── RIGHT: chat, vertical ─────────────── */}
          <section className="sim-right-panel">
            <header className="sim-right-header">
              <h2>Simulation Controller</h2>
              <p>Exercise-scoped chat. Coordinates monitoring, planning & resource agents.</p>
            </header>
            <div className="sim-right-chat">
              <SimulationChatPane
                tenantId={tenant.tenant_id}
                onScenarioCard={(card) => {
                  setScenarioCard(card as ScenarioCard);
                  logEvent(`Scenario seeded: ${(card as ScenarioCard).hazard ?? "scenario"}`);
                }}
                onEvent={logEvent}
              />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function Meter({
  label,
  value,
  limit,
  pct,
}: {
  label: string;
  value: number;
  limit?: number;
  pct: number;
}) {
  const barState = pct >= 90 ? "danger" : pct >= 75 ? "warn" : "ok";
  return (
    <div className="sim-meter">
      <div className="sim-meter-row">
        <span>{label}</span>
        <span className="sim-meter-value">
          {value}
          {limit !== undefined && <span className="sim-meter-limit"> / {limit}</span>}
        </span>
      </div>
      {limit !== undefined && (
        <div className="sim-meter-bar" aria-hidden="true">
          <span
            className={`sim-meter-bar-fill sim-meter-bar-fill--${barState}`}
            style={{ width: `${Math.min(100, pct)}%` }}
          />
        </div>
      )}
    </div>
  );
}
