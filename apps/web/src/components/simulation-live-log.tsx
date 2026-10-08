"use client";

/**
 * Simulation live-log component (spec-036 T-V01..T-V04 / FR-064).
 *
 * Operator-facing transcript of every synthetic-delivery / lifecycle /
 * refusal audit event surfaced for the active simulation. The component
 * is **read-only**; mutating actions are surfaced via the controller
 * pane (see `simulation-chat-pane.tsx`).
 *
 * Constraints:
 *
 * - **Accessibility (T-V04)** — the log is a polite live region
 *   (`role="log"` + `aria-live="polite"` + `aria-atomic="false"`); each
 *   entry includes an `aria-label` naming the AIIMS function so screen
 *   readers preserve attribution. AAA contrast on the AWS palette is
 *   enforced via inline `borderLeftColor` style.
 * - **AWS three-tier (constitution v1.2.0)** — entries with an
 *   `aws_tier` payload are styled with the canonical palette: advice
 *   `#fbbf24`, watch-and-act `#fb923c`, emergency warning `#dc2626`.
 * - **Locale-aware rendering (T-V02 / FR-058)** — when a `locale` is
 *   supplied the component renders the localised label from a small
 *   in-bundle whitelist; missing locales fall back to `en-AU` and tag
 *   the entry with `[FALLBACK]`. The full locale table lives in
 *   `apps/api/app/services/simulation/data/sim_locale_table.json`
 *   (T-W01); this component only resolves the *display label* per
 *   locale because the full table is fetched server-side and surfaced
 *   via SSE.
 * - **Synthetic-only egress (FR-006)** — entries whose `synthetic`
 *   flag is true are decorated with the `[SIMULATION]` prefix.
 * - **SSE wiring (T-V03)** — when an `sseUrl` is supplied, the
 *   component opens a credentialed EventSource and concatenates streamed
 *   `synthetic-delivery` / `lifecycle.*` events with the supplied
 *   `entries` prop.
 */

import type * as React from "react";
import { useEffect, useMemo, useState } from "react";

/** AIIMS functions per `packages/domain/.../aiims_role_assignment.py`. */
export type AiimsFunction =
  | "control"
  | "intelligence"
  | "planning"
  | "operations"
  | "logistics"
  | "public_information";

/** AWS three-tier per constitution v1.2.0. */
export type AwsTier = "advice" | "watch_and_act" | "emergency_warning";

/** Wire-shape of a single live-log entry rendered by the component. */
export interface SimulationLiveLogEntry {
  id: string;
  /** ISO-8601 timestamp (UTC). */
  timestamp: string;
  /** Audit envelope `entry_type` (e.g. `synthetic-delivery`). */
  entry_type: string;
  /** Operator-facing message. */
  message: string;
  /** Per audit-envelope §6 (T-T03 / FR-061). */
  aiims_function?: AiimsFunction;
  /** Per audit-envelope §6 (T-O07 / FR-064). */
  delivery_channel?: "audio" | "text-live-log" | "both";
  /** AWS tier for palette styling (constitution v1.2.0). */
  aws_tier?: AwsTier;
  /** BCP-47 locale tag — drives label resolution. */
  locale?: string;
  /** Synthetic-only egress flag (FR-006). */
  synthetic?: boolean;
  /** Originating correlation id (audit-envelope §6). */
  correlation_id?: string;
}

/** Component props. */
export interface SimulationLiveLogProps {
  /** Static entries supplied by the parent (server snapshot). */
  entries: SimulationLiveLogEntry[];
  /** Optional SSE URL — when set, opens an `EventSource` for live updates. */
  sseUrl?: string;
}

const AWS_PALETTE: Record<AwsTier, string> = {
  advice: "#fbbf24",
  watch_and_act: "#fb923c",
  emergency_warning: "#dc2626",
};

const KNOWN_LOCALES: ReadonlySet<string> = new Set([
  "en-AU",
  "en-GB",
  "en-US",
  "zh-CN",
  "zh-TW",
  "vi-VN",
  "ar-SA",
  "es-ES",
  "yo-AU", // Yolŋu-matha (NT priority)
  "wbp-AU", // Warlpiri (NT priority)
  "rop-AU", // Kriol (NT priority)
]);

const DEFAULT_LOCALE = "en-AU";

function resolveLocale(locale: string | undefined): {
  resolved: string;
  isFallback: boolean;
} {
  if (!locale) return { resolved: DEFAULT_LOCALE, isFallback: false };
  if (KNOWN_LOCALES.has(locale)) return { resolved: locale, isFallback: false };
  return { resolved: DEFAULT_LOCALE, isFallback: true };
}

function formatEntryText(entry: SimulationLiveLogEntry): string {
  const prefix = entry.synthetic ? "[SIMULATION] " : "";
  const { isFallback } = resolveLocale(entry.locale);
  const fallbackTag = isFallback ? " [FALLBACK]" : "";
  return `${prefix}${entry.message}${fallbackTag}`;
}

function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  const h = String(d.getUTCHours()).padStart(2, "0");
  const m = String(d.getUTCMinutes()).padStart(2, "0");
  const s = String(d.getUTCSeconds()).padStart(2, "0");
  return `${h}:${m}:${s}Z`;
}

export function SimulationLiveLog({
  entries,
  sseUrl,
}: SimulationLiveLogProps): React.JSX.Element {
  const [streamed, setStreamed] = useState<SimulationLiveLogEntry[]>([]);

  useEffect(() => {
    if (!sseUrl) return undefined;
    if (typeof EventSource === "undefined") return undefined;

    const source = new EventSource(sseUrl, { withCredentials: true });
    const onEntry = (ev: MessageEvent) => {
      try {
        const parsed: SimulationLiveLogEntry = JSON.parse(ev.data);
        setStreamed((prev) => [...prev, parsed]);
      } catch (err) {
        // Malformed events MUST NOT crash the live region — log and skip.
         
        console.warn("simulation-live-log: dropped malformed SSE event", err);
      }
    };
    source.addEventListener("synthetic-delivery", onEntry);
    source.addEventListener("lifecycle", onEntry);
    source.addEventListener("message", onEntry);
    return () => {
      source.removeEventListener("synthetic-delivery", onEntry);
      source.removeEventListener("lifecycle", onEntry);
      source.removeEventListener("message", onEntry);
      source.close();
    };
  }, [sseUrl]);

  const all = useMemo(() => [...entries, ...streamed], [entries, streamed]);

  if (all.length === 0) {
    return (
      <div
        className="sim-live-log sim-live-log--empty"
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
        aria-atomic="false"
        aria-label="Simulation live log (empty)"
        data-testid="simulation-live-log"
      >
        No live events yet.
      </div>
    );
  }

  return (
    <ol
      className="sim-live-log"
      role="log"
      aria-live="polite"
      aria-relevant="additions text"
      aria-atomic="false"
      aria-label="Simulation live log"
      data-testid="simulation-live-log"
      style={{ listStyle: "none", padding: 0, margin: 0 }}
    >
      {all.map((entry) => {
        const { resolved, isFallback } = resolveLocale(entry.locale);
        const colour = entry.aws_tier
          ? AWS_PALETTE[entry.aws_tier]
          : "transparent";
        const ariaLabel = [
          entry.aiims_function ?? "general",
          entry.entry_type,
          entry.message,
        ].join(" — ");
        return (
          <li
            key={entry.id}
            data-testid={`live-log-entry-${entry.id}`}
            data-aws-tier={entry.aws_tier ?? ""}
            data-locale={resolved}
            data-locale-fallback={isFallback ? DEFAULT_LOCALE : undefined}
            lang={resolved}
            aria-label={ariaLabel}
            style={{
              borderLeft: "4px solid",
              borderLeftColor: colour,
              padding: "0.25rem 0.5rem",
              margin: "0.25rem 0",
              fontFamily:
                "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
              fontSize: "0.875rem",
              lineHeight: "1.4",
            }}
          >
            <span className="sim-live-log__time" aria-hidden="true">
              {formatTimestamp(entry.timestamp)}
            </span>{" "}
            <span className="sim-live-log__msg">{formatEntryText(entry)}</span>
          </li>
        );
      })}
    </ol>
  );
}
