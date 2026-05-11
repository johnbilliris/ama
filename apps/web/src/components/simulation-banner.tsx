"use client";

/**
 * Spec-036 T-I07 — paused / aborted / archived state surfacing.
 *
 * The base "Exercise mode" banner remains the static visual watermark
 * (FR-058). When the simulation transitions into a paused, aborted, or
 * archived state via a `lifecycle.*` audit envelope (FR-059), the banner
 * adds a high-contrast status pill plus a structured message that is
 * keyboard-focusable (`tabIndex={0}`) and announced via `role="alert"`.
 */
import type { LifecycleEventType } from "@/lib/sse";

type LifecycleStatus = "active" | "paused" | "aborted" | "archived" | "completed";

const STATUS_BY_EVENT: Record<LifecycleEventType, LifecycleStatus> = {
  "lifecycle.scenario_started": "active",
  "lifecycle.scenario_paused": "paused",
  "lifecycle.scenario_resumed": "active",
  "lifecycle.scenario_aborted": "aborted",
  "lifecycle.scenario_archived": "archived",
  "lifecycle.scenario_completed": "completed",
};

const STATUS_META: Record<
  LifecycleStatus,
  { label: string; tone: string; aria: string; icon: string }
> = {
  active: {
    label: "Active",
    tone: "bg-emerald-100 text-emerald-900 ring-emerald-300",
    aria: "Simulation exercise active",
    icon: "▶",
  },
  paused: {
    label: "Paused",
    tone: "bg-amber-100 text-amber-900 ring-amber-300",
    aria: "Simulation exercise paused",
    icon: "⏸",
  },
  aborted: {
    label: "Aborted",
    tone: "bg-red-100 text-red-900 ring-red-300",
    aria: "Simulation exercise aborted",
    icon: "⛔",
  },
  archived: {
    label: "Archived",
    tone: "bg-slate-200 text-slate-900 ring-slate-400",
    aria: "Simulation exercise archived (read-only)",
    icon: "📦",
  },
  completed: {
    label: "Completed",
    tone: "bg-blue-100 text-blue-900 ring-blue-300",
    aria: "Simulation exercise completed",
    icon: "✓",
  },
};

interface SimulationBannerProps {
  /** Latest `lifecycle.*` event, if any. */
  lifecycleEvent?: { event_type: LifecycleEventType; reason?: string; actor?: string };
}

export function SimulationBanner({ lifecycleEvent }: SimulationBannerProps = {}) {
  const status: LifecycleStatus = lifecycleEvent
    ? (STATUS_BY_EVENT[lifecycleEvent.event_type] ?? "active")
    : "active";
  const meta = STATUS_META[status];
  const isAlert = status === "paused" || status === "aborted";
  return (
    <div
      className="sim-banner-wrap"
      role={isAlert ? "alert" : "status"}
      aria-live={isAlert ? "assertive" : "polite"}
    >
      <div className="sim-banner-card">
        <div className="flex items-center gap-2">
          <p className="sim-banner-kicker">⚠ Exercise mode</p>
          <span
            tabIndex={0}
            data-testid="sim-banner-status"
            data-status={status}
            aria-label={meta.aria}
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 focus:outline-none focus:ring-2 focus:ring-offset-1 ${meta.tone}`}
          >
            <span aria-hidden="true">{meta.icon}</span>
            <span>{meta.label}</span>
          </span>
        </div>
        <h2 className="sim-banner-title">Simulation — this is not live data</h2>
        <p className="sim-banner-copy">
          All communications, decisions and telemetry on this page are scoped to
          the exercise tenant. No real-world dispatch or public notifications
          will be issued.
        </p>
        {lifecycleEvent?.reason && (status === "paused" || status === "aborted") && (
          <p
            data-testid="sim-banner-reason"
            className="sim-banner-copy mt-1 text-[11px] font-medium"
          >
            {meta.label} — {lifecycleEvent.reason}
            {lifecycleEvent.actor ? ` (by ${lifecycleEvent.actor})` : ""}
          </p>
        )}
      </div>
    </div>
  );
}
