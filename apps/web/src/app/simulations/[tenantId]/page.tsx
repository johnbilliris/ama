"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
import { getPlaybackEvents, recordEventLogEntry, type PlaybackEvent } from "@/lib/api/simulation-playback";
import { useReportSimulationLifecycle } from "@/components/simulation-lifecycle";
import { SimulationChatPane } from "@/components/simulation-chat-pane";
import { SimulationMap, type ScenarioCard } from "@/components/simulation-map";
import { SimulationPersonaWorkspace } from "@/components/simulation-persona-workspace";
import { SimulationServerClock } from "@/components/simulation-server-clock";
import { SimulationWarpControls } from "@/components/simulation-warp-controls";
import { SIMULATION_REFRESH_INTERVAL_MS } from "@/lib/simulation-refresh";

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

// AUD-016 / US3-AS4 — shared exercise activity must become visible to other
// participants within five seconds, so the event poll runs at that cadence.
const EVENT_LOG_POLL_INTERVAL_MS = SIMULATION_REFRESH_INTERVAL_MS;

interface EventLogEntry {
  /** Stable key — server `event_seq` (`server-<n>`) or local timestamp. */
  id: string;
  ts: string;
  text: string;
  /** True when sourced from the Cosmos `sim-events` container (durable). */
  persisted: boolean;
}

/**
 * Render a one-line, human-friendly summary of a SimulationEvent payload
 * so the right-hand Event Log can replay activity originally produced by
 * other operators (or by the same operator before a refresh).
 */
function describePlaybackEvent(ev: PlaybackEvent): string {
  const p = ev.payload ?? {};
  switch (ev.event_type) {
    case "chat_turn_user": {
      const preview = String(p.message_preview ?? "").trim();
      return preview ? `Command issued: ${preview}` : "Command issued";
    }
    case "chat_turn_assistant":
      return "Controller reply complete";
    case "tool_invocation": {
      const tool = String(p.tool_name ?? "tool");
      return `Tool invoked: ${tool}`;
    }
    case "state_change": {
      const to = String(p.to_status ?? "");
      const from = String(p.from_status ?? "");
      return `Simulation ${to.toLowerCase() || "state changed"}${from ? ` (was ${from})` : ""}`;
    }
    case "warp_speed_change": {
      const speed = p.new_speed ?? p.warp_speed ?? p.speed;
      return speed !== undefined ? `Warp speed changed to ${speed}×` : "Warp speed changed";
    }
    case "signal_delivered": {
      const cat = String(p.category ?? "signal");
      return `Signal delivered: ${cat}`;
    }
    case "annotation":
      return `Annotation: ${String(p.text ?? "").slice(0, 80)}`;
    case "ui_log":
      return String(p.text ?? "").slice(0, 200);
    default:
      return ev.event_type.replaceAll("_", " ");
  }
}

export default function SimulationDashboardPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const [tenant, setTenant] = useState<SimulationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scenarioCard, setScenarioCard] = useState<ScenarioCard | null>(null);
  const [eventLog, setEventLog] = useState<EventLogEntry[]>([]);
  const [eventLogOpen, setEventLogOpen] = useState(true);
  const [currentWarpSpeed, setCurrentWarpSpeed] = useState<number>(1);
  // Highest persisted event_seq we've already merged. Lets the polling
  // loop ask Cosmos only for new events rather than re-fetching the
  // whole stream every tick.
  const lastSeqRef = useRef<number>(0);

  const logEvent = useCallback(
    (text: string, category?: string) => {
      setEventLog((prev) => [
        ...prev,
        { id: `local-${Date.now()}-${prev.length}`, ts: new Date().toISOString(), text, persisted: false },
      ]);
      // Permanent fix: mirror every UI-emitted line into the durable
      // ``sim-events`` Cosmos container so a refresh (or post-exercise
      // review) shows the full history, not just whatever happens to be
      // captured by the back-end's typed event recorders.
      if (tenantId) {
        void recordEventLogEntry(tenantId, text, category);
      }
    },
    [tenantId],
  );

  const refreshPersistedEvents = useCallback(async () => {
    if (!tenantId) return;
    try {
      const page = await getPlaybackEvents(tenantId, lastSeqRef.current, 200, true);
      if (page.events.length === 0) return;
      const newEntries: EventLogEntry[] = page.events.map((ev) => ({
        id: `server-${ev.event_seq}`,
        ts: ev.wall_clock_time,
        text: describePlaybackEvent(ev),
        persisted: true,
      }));
      lastSeqRef.current = Math.max(
        lastSeqRef.current,
        ...page.events.map((e) => e.event_seq),
      );
      setEventLog((prev) => {
        const seenIds = new Set(newEntries.map((e) => e.id));
        // Drop any server entries we already inserted (re-poll overlap)
        // AND any optimistic local entries older than the newest server
        // event — by then, anything that was going to be persisted will
        // have shown up server-side, so a stale local twin is just noise.
        const newestServerTs = newEntries[newEntries.length - 1]?.ts;
        const pruned = prev.filter((e) => {
          if (e.persisted && seenIds.has(e.id)) return false;
          if (!e.persisted && newestServerTs && e.ts < newestServerTs) return false;
          return true;
        });
        return [...pruned, ...newEntries].sort((a, b) =>
          a.ts.localeCompare(b.ts),
        );
      });
    } catch (err) {
      // Failure to read events must never break the dashboard. Keep the
      // local log alive so the operator can still see UI-side activity.
      console.warn("event log refresh failed", err);
    }
  }, [tenantId]);

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

  // Hydrate the Event Log from Cosmos on mount, then poll for new events
  // so commands issued from the chat pane (and lifecycle changes from any
  // other tab/operator) appear without a manual refresh.
  useEffect(() => {
    if (!tenantId) return;
    let cancelled = false;
    void refreshPersistedEvents();
    const id = setInterval(() => {
      if (!cancelled) void refreshPersistedEvents();
    }, EVENT_LOG_POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [tenantId, refreshPersistedEvents]);

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

  // AUD-018 — the /simulations layout owns the marker; publish the real
  // lifecycle so it never advertises "Active" for an archived exercise.
  useReportSimulationLifecycle(tenant?.status ?? null);

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

  const cacheKeys = tenant.resource_consumption.cache_keys ?? null;
  const assignments = tenant.participant_assignments ?? [];
  const assignedOids = new Set(assignments.map((a) => a.oid));
  const unassignedParticipants = tenant.participants.filter((oid) => !assignedOids.has(oid));

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
    setTimeout(() => void refreshPersistedEvents(), 1500);
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
    setTimeout(() => void refreshPersistedEvents(), 1500);
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
    setTimeout(() => void refreshPersistedEvents(), 1500);
  };

  return (
    <div className="sim-dashboard-page">
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
                  setTimeout(() => void refreshPersistedEvents(), 1500);
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
              {tenant.throttle_notice && (
                <p
                  role="status"
                  data-testid="sim-throttle-notice"
                  className="sim-panel-empty"
                >
                  {tenant.throttle_notice}
                </p>
              )}
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
                    <span>Cache keys</span>
                    <span
                      className="sim-meter-value"
                      data-testid="sim-cache-keys"
                      title={
                        cacheKeys == null
                          ? "The API did not report a simulation cache-key count."
                          : "Count as reported by the simulation API."
                      }
                    >
                      {cacheKeys == null
                        ? "Not reported"
                        : cacheKeys === 0
                          ? "None reported"
                          : cacheKeys}
                    </span>
                  </div>
                </div>
                <div className="sim-meter">
                  <div className="sim-meter-row">
                    <span>Throttle</span>
                    <span className="sim-meter-value" data-testid="sim-throttle-status">
                      {tenant.throttle_mode} · {tenant.throttle_quota_pct}% quota
                    </span>
                  </div>
                </div>                <div className="sim-meter">
                  <div className="sim-meter-row">
                    <span>Participants</span>
                    <span className="sim-meter-value">{tenant.participants.length}</span>
                  </div>
                </div>
              </div>
            </section>

            <SimulationPersonaWorkspace
              assignments={assignments}
              unassignedParticipants={unassignedParticipants}
              tenantId={tenantId}
            />

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
                {["Archived", "Completed"].includes(tenant.status) && (
                  <Link
                    href={`/simulations/${tenant.tenant_id}/playback`}
                    className="sim-panel-backlink"
                  >
                    ▶ Review Playback
                  </Link>
                )}
                {tenant.exercise_report_id ? (
                  <Link
                    href={`/simulations/reports/${tenant.exercise_report_id}`}
                    className="sim-panel-backlink"
                    data-testid="sim-report-link"
                  >
                    📄 View exercise report
                  </Link>
                ) : (
                  ["Archived", "Archiving", "Completed"].includes(tenant.status) && (
                    <span className="sim-panel-empty" data-testid="sim-report-pending">
                      Exercise report not yet available.
                    </span>
                  )
                )}
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
                      {eventLog.map((ev) => (
                        <li key={ev.id}>
                          <span className="sim-event-ts">
                            {new Date(ev.ts).toLocaleTimeString()}
                          </span>
                          <span className="sim-event-text">{ev.text}</span>
                          {!ev.persisted && (
                            <span
                              className="sim-event-pending"
                              title="Local event — not yet stored in Cosmos"
                              aria-label="local only"
                            >
                              ·
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </section>

            {/* AUD-016 — the browser-only "Exercise Objectives" list was removed.
                It looked like durable coordination state but never persisted,
                so it disappeared on reload and was invisible to other
                participants. Reinstate only behind a server-backed store. */}
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
                  // Server records `signal_delivered` events when the
                  // scenario seeds — pull them in so the Event Log shows
                  // the seed activity, not just our optimistic line.
                  setTimeout(() => {
                    void refreshPersistedEvents();
                  }, 1500);
                }}
                onEvent={(text) => {
                  logEvent(text);
                  // Each user prompt and assistant reply is now persisted
                  // server-side as chat_turn_user / chat_turn_assistant /
                  // tool_invocation events. Refetch shortly after the
                  // event fires so the durable rows replace our optimistic
                  // local entries (which are then deduped by event id).
                  setTimeout(() => {
                    void refreshPersistedEvents();
                  }, 1500);
                }}
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
