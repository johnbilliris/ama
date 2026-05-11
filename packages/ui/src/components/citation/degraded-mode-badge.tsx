/**
 * Spec 036 T085 / T133 — Degraded mode badge.
 *
 * Surfaces an offline / stale-cache / retrieval-unavailable banner when the
 * agent surface is operating from the offline cache (FR-RAG-LS-02) or with
 * AI Search unreachable (FR-RAG-FM-04 fail-closed). The badge has three
 * canonical states keyed off the ``mode`` prop:
 *
 *   1. ``offline-cache-active`` — Field Coordinator is running from a signed
 *      offline bundle. Show cache build age (relative + absolute) and the
 *      jurisdiction label so the operator knows which handbook scope is
 *      authoritative.
 *   2. ``stale-cache`` — Cache is past its 11-day stale warning but still
 *      within the 14-day fail-closed window. Escalates the visual severity.
 *   3. ``retrieval-unavailable`` — AI Search returned an error and there is
 *      no offline fallback; the agent has degraded to a citation-less
 *      response with a confidence-downgrade applied.
 *
 * Accessibility (WCAG 2.2 AA, FR-RAG-UX-04):
 *   - Banner uses ``role="alert"`` so screen readers announce the degraded
 *     state on render.
 *   - Each state carries a stable ``data-degraded-mode`` attribute so the
 *     a11y test (``tests/e2e/degraded_mode_badge.spec.ts``) can pin
 *     selectors.
 *   - Colour-on-colour contrast verified via axe-core in CI.
 *   - Jurisdiction is rendered with the full name expansion (e.g.
 *     ``NSW (New South Wales)``) so non-AU operators / screen-readers don't
 *     have to decode the ISO 3166-2 sub-code.
 *   - Stale-cache age is rendered as both relative ("12 minutes old") and
 *     absolute ("since 14:32 AEDT") to satisfy operator audit requirements
 *     and CALD operators who prefer absolute timestamps.
 */

export type DegradedModeKind =
  | "offline-cache-active"
  | "stale-cache"
  | "retrieval-unavailable";

const JURISDICTION_LABELS: Record<string, string> = {
  act: "ACT (Australian Capital Territory)",
  nsw: "NSW (New South Wales)",
  nt: "NT (Northern Territory)",
  qld: "QLD (Queensland)",
  sa: "SA (South Australia)",
  tas: "TAS (Tasmania)",
  vic: "VIC (Victoria)",
  wa: "WA (Western Australia)",
  national: "National",
  aidr: "AIDR (Australian Disaster Resilience)",
};

export interface DegradedModeBadgeProps {
  /** When true, render the banner; otherwise render nothing. */
  degraded: boolean;
  /**
   * Which degraded state to render. Defaults to ``offline-cache-active``
   * for backward compatibility with the original scaffold.
   */
  mode?: DegradedModeKind;
  /** Optional ISO-8601 timestamp of the cache manifest. */
  cacheBuiltAt?: string;
  /** Optional human-readable note (e.g. "Foundry endpoint unreachable"). */
  reason?: string;
  /**
   * Jurisdiction code (lower-case, e.g. "nsw", "aidr"). Expanded to the
   * full name for accessibility.
   */
  jurisdiction?: string;
  /** Days remaining before the 14-day TTL fail-closes. */
  ttlDaysRemaining?: number;
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

function expandJurisdiction(code?: string): string {
  if (!code) return "";
  const key = code.toLowerCase();
  return JURISDICTION_LABELS[key] ?? code.toUpperCase();
}

interface BadgeStyle {
  border: string;
  bg: string;
  fg: string;
  fgMuted: string;
  iconChar: string;
  title: string;
}

function styleFor(mode: DegradedModeKind): BadgeStyle {
  switch (mode) {
    case "stale-cache":
      // Higher severity — past 11-day stale warning.
      return {
        border: "border-orange-600",
        bg: "bg-orange-50",
        fg: "text-orange-900",
        fgMuted: "text-orange-800",
        iconChar: "!",
        title: "Cache is stale — refresh required",
      };
    case "retrieval-unavailable":
      // Highest severity — no grounding source available at all.
      return {
        border: "border-red-700",
        bg: "bg-red-50",
        fg: "text-red-900",
        fgMuted: "text-red-800",
        iconChar: "!",
        title: "Retrieval unavailable — confidence downgraded",
      };
    case "offline-cache-active":
    default:
      return {
        border: "border-amber-500",
        bg: "bg-amber-50",
        fg: "text-amber-900",
        fgMuted: "text-amber-800",
        iconChar: "!",
        title: "Operating from offline cache",
      };
  }
}

export function DegradedModeBadge({
  degraded,
  mode = "offline-cache-active",
  cacheBuiltAt,
  reason,
  jurisdiction,
  ttlDaysRemaining,
  className,
}: DegradedModeBadgeProps) {
  if (!degraded) return null;
  const relative = formatRelative(cacheBuiltAt);
  const absolute = formatAbsolute(cacheBuiltAt);
  const jurLabel = expandJurisdiction(jurisdiction);
  const style = styleFor(mode);

  // Body lines are computed per-mode so each path renders the right detail
  // for an assistive-technology user.
  const lines: string[] = [];
  if (mode === "offline-cache-active" || mode === "stale-cache") {
    let cacheLine = `Showing cached corpus content (${relative}`;
    if (absolute) cacheLine += `, since ${absolute}`;
    cacheLine += ").";
    lines.push(cacheLine);
    if (typeof ttlDaysRemaining === "number") {
      lines.push(
        `${ttlDaysRemaining} day${ttlDaysRemaining === 1 ? "" : "s"} remaining before mandatory refresh.`,
      );
    }
  } else {
    lines.push(
      "AI Search retrieval failed; the recommendation below was generated without grounding citations.",
    );
  }
  if (jurLabel) lines.push(`Jurisdiction scope: ${jurLabel}.`);
  if (reason) lines.push(reason);

  const guidance =
    mode === "retrieval-unavailable"
      ? "Confidence has been downgraded. Do NOT issue any life-safety directive on the basis of this response — verify against the source handbook first."
      : "Recommendations may not reflect the latest handbook updates. Verify any life-safety guidance against the source document before issuing a directive.";

  return (
    <div
      role="alert"
      data-degraded-mode={mode}
      className={`flex items-start gap-2 rounded border-l-4 ${style.border} ${style.bg} px-3 py-2 text-sm ${style.fg} ${className ?? ""}`}
    >
      <span aria-hidden="true" className="text-base font-bold">
        {style.iconChar}
      </span>
      <div className="flex flex-col">
        <strong className="font-semibold">{style.title}</strong>
        {lines.map((l, i) => (
          <span key={i}>{l}</span>
        ))}
        <span className={`text-xs ${style.fgMuted}`}>{guidance}</span>
      </div>
    </div>
  );
}

export default DegradedModeBadge;
