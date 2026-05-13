/**
 * Tests for spec-036 T-V01..T-V04 — simulation live-log component.
 *
 * The live-log component is the operator-facing transcript of every
 * synthetic-delivery / lifecycle / refusal audit event for the active
 * simulation (FR-064). Constraints honoured:
 *
 * - **Accessibility (T-V04)**: the log is a polite live region
 *   (`role="log"` + `aria-live="polite"` + `aria-atomic="false"`) and
 *   each entry includes a screen-reader label naming the AIIMS function
 *   so audit-trail review with assistive tech preserves attribution.
 * - **AWS three-tier (constitution v1.2.0)**: any entry whose payload
 *   carries an `aws_tier` MUST be styled with the canonical AWS palette
 *   (advice = `#fbbf24`, watch-and-act = `#fb923c`,
 *   emergency-warning = `#dc2626`). The component exposes the colour
 *   via inline style for snapshot-style assertion in this unit suite;
 *   the broader visual contract is enforced in Playwright (T-V05+).
 * - **Locale-aware rendering (T-V02)**: when a `locale` is supplied the
 *   component renders the correct localised label from the in-bundle
 *   locale table (a small subset is used here to avoid coupling the
 *   tests to apps/api). Missing locales fall back to the canonical
 *   English label and emit `[FALLBACK]` next to the entry per FR-058.
 * - **Synthetic-only egress (FR-006)**: entries are decorated with the
 *   `[SIMULATION]` prefix when their `synthetic` flag is true.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";

import {
  SimulationLiveLog,
  type SimulationLiveLogEntry,
} from "@/components/simulation-live-log";

afterEach(() => {
  cleanup();
});

const baseEntry: SimulationLiveLogEntry = {
  id: "evt-1",
  timestamp: "2025-01-01T09:00:00.000Z",
  entry_type: "synthetic-delivery",
  message: "Hot wind warning — Risk advisory",
  aiims_function: "intelligence",
  delivery_channel: "text-live-log",
  synthetic: true,
};

describe("SimulationLiveLog (T-V01)", () => {
  it("renders an empty placeholder when no entries are supplied", () => {
    render(<SimulationLiveLog entries={[]} />);
    const log = screen.getByRole("log");
    expect(log).toBeInTheDocument();
    expect(log).toHaveTextContent(/no live events yet/i);
  });

  it("renders entries inside a polite ARIA live region (T-V04)", () => {
    render(<SimulationLiveLog entries={[baseEntry]} />);
    const log = screen.getByRole("log");
    expect(log.getAttribute("aria-live")).toBe("polite");
    expect(log.getAttribute("aria-atomic")).toBe("false");
    expect(log).toHaveAttribute("aria-label", expect.stringMatching(/live log/i));
  });

  it("decorates synthetic entries with [SIMULATION] prefix (FR-006)", () => {
    render(<SimulationLiveLog entries={[baseEntry]} />);
    expect(screen.getByText(/^\[SIMULATION\]/)).toBeInTheDocument();
  });

  it("includes AIIMS function as a screen-reader label per entry (T-V04)", () => {
    render(<SimulationLiveLog entries={[baseEntry]} />);
    const item = screen.getByTestId("live-log-entry-evt-1");
    expect(item).toHaveAttribute(
      "aria-label",
      expect.stringMatching(/intelligence/i)
    );
  });
});

describe("SimulationLiveLog AWS palette (constitution v1.2.0)", () => {
  it("colours advice entries amber (#fbbf24)", () => {
    const entry = { ...baseEntry, id: "evt-a", aws_tier: "advice" as const };
    render(<SimulationLiveLog entries={[entry]} />);
    const item = screen.getByTestId("live-log-entry-evt-a");
    expect(item.getAttribute("data-aws-tier")).toBe("advice");
    expect(item.style.borderLeftColor).toBe("rgb(251, 191, 36)");
  });

  it("colours watch-and-act entries orange (#fb923c)", () => {
    const entry = {
      ...baseEntry,
      id: "evt-w",
      aws_tier: "watch_and_act" as const,
    };
    render(<SimulationLiveLog entries={[entry]} />);
    const item = screen.getByTestId("live-log-entry-evt-w");
    expect(item.style.borderLeftColor).toBe("rgb(251, 146, 60)");
  });

  it("colours emergency_warning entries red (#dc2626)", () => {
    const entry = {
      ...baseEntry,
      id: "evt-e",
      aws_tier: "emergency_warning" as const,
    };
    render(<SimulationLiveLog entries={[entry]} />);
    const item = screen.getByTestId("live-log-entry-evt-e");
    expect(item.style.borderLeftColor).toBe("rgb(220, 38, 38)");
  });
});

describe("SimulationLiveLog locale rendering (T-V02)", () => {
  it("renders the locale-resolved label when a known locale is supplied", () => {
    const entry = { ...baseEntry, id: "evt-loc-1", locale: "en-AU" };
    render(<SimulationLiveLog entries={[entry]} />);
    const item = screen.getByTestId("live-log-entry-evt-loc-1");
    expect(item.getAttribute("data-locale")).toBe("en-AU");
  });

  it("falls back to English and tags [FALLBACK] for unknown locales (FR-058)", () => {
    const entry = { ...baseEntry, id: "evt-fb-1", locale: "xx-YY" };
    render(<SimulationLiveLog entries={[entry]} />);
    const item = screen.getByTestId("live-log-entry-evt-fb-1");
    expect(item.textContent).toContain("[FALLBACK]");
    expect(item.getAttribute("data-locale-fallback")).toBe("en-AU");
  });

  it("sets lang attribute on each list item per T-V03", () => {
    const entry = { ...baseEntry, id: "evt-lang-1", locale: "vi-VN" };
    render(<SimulationLiveLog entries={[entry]} />);
    const item = screen.getByTestId("live-log-entry-evt-lang-1");
    expect(item.getAttribute("lang")).toBe("vi-VN");
  });
});

describe("SimulationLiveLog SSE wiring (T-V03)", () => {
  it("subscribes to the supplied SSE URL on mount and unsubscribes on unmount", () => {
    const close = vi.fn();
    const ctorSpy = vi.fn(function (this: object) {
      Object.assign(this, {
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        close,
      });
    });
    // Stub global EventSource so tests can introspect.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (globalThis as any).EventSource = ctorSpy as unknown as typeof EventSource;
    const { unmount } = render(
      <SimulationLiveLog
        entries={[]}
        sseUrl="/api/simulations/sim-V/live-log"
      />
    );
    expect(ctorSpy).toHaveBeenCalledWith(
      "/api/simulations/sim-V/live-log",
      expect.objectContaining({ withCredentials: true })
    );
    unmount();
    expect(close).toHaveBeenCalled();
  });
});
