/**
 * Spec 036 T085 — Degraded mode badge (initial scaffold).
 *
 * Surfaces an offline / stale-cache banner when the agent surface is
 * operating from the offline cache (FR-RAG-LS-02). Full degraded-mode
 * UX (icon, drawer, manifest hash tooltip) lands in Phase D4; this scaffold
 * exists so:
 *
 *   - the recommendation cards can wire it in now without UI churn later,
 *   - the WCAG 2.2 AA review (T101) covers the colour + label combo,
 *   - the offline-cache feature has a visible signal from day one.
 *
 * Accessibility:
 *   - Banner uses role="alert" so screen readers announce the degraded state.
 *   - Stale-cache age is rendered as both relative ("12 minutes old") and
 *     absolute ("since 14:32 AEDT") to satisfy operator audit requirements.
 */

export interface DegradedModeBadgeProps {
  /** When true, render the banner; otherwise render nothing. */
  degraded: boolean;
  /** Optional ISO-8601 timestamp of the cache manifest. */
  cacheBuiltAt?: string;
  /** Optional human-readable note (e.g. "Foundry endpoint unreachable"). */
  reason?: string;
  className?: string;
}

function formatRelative(iso?: string): string {
  if (!iso) return "unknown age";
  const ts = Date.parse(iso);
  if (Number.isNaN(ts)) return "unknown age";
  const diffMs = Date.now() - ts;
  const minutes = Math.max(0, Math.round(diffMs / 60000));
  if (minutes < 1) return "less than a minute old";
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} old`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} old`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} old`;
}

function formatAbsolute(iso?: string): string {
  if (!iso) return "";
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return "";
  return dt.toLocaleString("en-AU", { timeZone: "Australia/Sydney" });
}

export function DegradedModeBadge({
  degraded,
  cacheBuiltAt,
  reason,
  className,
}: DegradedModeBadgeProps) {
  if (!degraded) return null;
  const relative = formatRelative(cacheBuiltAt);
  const absolute = formatAbsolute(cacheBuiltAt);
  return (
    <div
      role="alert"
      className={`flex items-start gap-2 rounded border-l-4 border-amber-500 bg-amber-50 px-3 py-2 text-sm text-amber-900 ${className ?? ""}`}
    >
      <span aria-hidden="true" className="text-base">⚠</span>
      <div className="flex flex-col">
        <strong className="font-semibold">Operating in degraded mode</strong>
        <span>
          Showing cached corpus content ({relative}
          {absolute ? `, since ${absolute}` : ""}).
          {reason ? ` ${reason}.` : ""}
        </span>
        <span className="text-xs text-amber-800">
          Recommendations may not reflect the latest handbook updates. Verify any life-safety guidance
          against the source document before issuing a directive.
        </span>
      </div>
    </div>
  );
}

export default DegradedModeBadge;
