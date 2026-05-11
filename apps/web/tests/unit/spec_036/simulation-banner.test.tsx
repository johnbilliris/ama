/**
 * Spec-036 T-I07 — simulation-banner lifecycle status tests.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { SimulationBanner } from "@/components/simulation-banner";

describe("SimulationBanner lifecycle states", () => {
  it("defaults to active when no lifecycle event is supplied", () => {
    render(<SimulationBanner />);
    const status = screen.getByTestId("sim-banner-status");
    expect(status.getAttribute("data-status")).toBe("active");
    expect(status.getAttribute("aria-label")).toContain("active");
  });

  it("surfaces paused state with role=alert and reason copy", () => {
    render(
      <SimulationBanner
        lifecycleEvent={{
          event_type: "lifecycle.scenario_paused",
          reason: "controller break",
          actor: "ops-1",
        }}
      />,
    );
    const status = screen.getByTestId("sim-banner-status");
    expect(status.getAttribute("data-status")).toBe("paused");
    expect(screen.getByTestId("sim-banner-reason")).toHaveTextContent(
      /controller break/i,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("surfaces aborted state with reason and actor", () => {
    render(
      <SimulationBanner
        lifecycleEvent={{
          event_type: "lifecycle.scenario_aborted",
          reason: "real-event escalation",
          actor: "controller-12",
        }}
      />,
    );
    expect(
      screen.getByTestId("sim-banner-status").getAttribute("data-status"),
    ).toBe("aborted");
    expect(screen.getByTestId("sim-banner-reason")).toHaveTextContent(
      /real-event escalation/i,
    );
  });

  it("status pill is keyboard-focusable (tabIndex=0)", () => {
    render(<SimulationBanner />);
    expect(
      screen.getByTestId("sim-banner-status").getAttribute("tabindex"),
    ).toBe("0");
  });
});
