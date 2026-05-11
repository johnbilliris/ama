/**
 * Spec-036 T-I02 — unit tests for the three simulation badges.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { SimBadge } from "@/components/SimBadge";
import { StaleBadge } from "@/components/StaleBadge";
import { SimulationReceiptBadge } from "@/components/SimulationReceiptBadge";

describe("SimBadge", () => {
  it("renders [SIMULATION] watermark with role and aria label", () => {
    render(<SimBadge />);
    const badge = screen.getByTestId("sim-badge");
    expect(badge).toHaveTextContent("[SIMULATION]");
    expect(badge.getAttribute("role")).toBe("status");
    expect(badge.getAttribute("aria-label")).toBe("Simulation exercise mode");
  });

  it("supports a larger size variant", () => {
    render(<SimBadge size="md" />);
    expect(screen.getByTestId("sim-badge").className).toContain("text-[11px]");
  });
});

describe("StaleBadge", () => {
  it("returns null when below the freshness threshold", () => {
    const { container } = render(<StaleBadge ageSeconds={60} thresholdSeconds={300} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders aria-label with minute count when stale", () => {
    render(<StaleBadge ageSeconds={420} thresholdSeconds={300} />);
    const badge = screen.getByTestId("stale-badge");
    expect(badge).toHaveTextContent("STALE · 7m");
    expect(badge.getAttribute("aria-label")).toContain("7 minutes old");
  });
});

describe("SimulationReceiptBadge", () => {
  const allStatuses = ["queued", "sent", "delivered", "read", "failed"] as const;

  it.each(allStatuses)("renders %s status with descriptive aria-label", (status) => {
    render(<SimulationReceiptBadge status={status} />);
    const badge = screen.getByTestId("simulation-receipt-badge");
    expect(badge.getAttribute("data-status")).toBe(status);
    expect(badge.getAttribute("aria-label")).toContain("simulation");
  });

  it("includes channel in the aria label when provided", () => {
    render(<SimulationReceiptBadge status="delivered" channel="EAS" />);
    expect(
      screen.getByTestId("simulation-receipt-badge").getAttribute("aria-label"),
    ).toContain("EAS");
  });
});
