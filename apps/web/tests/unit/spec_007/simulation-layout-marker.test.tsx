/**
 * AUD-018 — the /simulations layout owns simulation identification for every
 * route and UI state, and reports real lifecycle rather than always "Active".
 */
import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import SimulationsLayout from "@/app/simulations/layout";
import {
  toLifecycleStatus,
  useReportSimulationLifecycle,
} from "@/components/simulation-lifecycle";

function Reporter({ status }: { status?: string | null }) {
  useReportSimulationLifecycle(status);
  return <p>route content</p>;
}

describe("simulations route layout marker", () => {
  it.each([
    ["loading", <div key="l">Loading simulation dashboard...</div>],
    ["error", <div key="e">Error loading simulation</div>],
    ["playback", <div key="p">Playback</div>],
    ["report", <div key="r">Exercise Report</div>],
  ])("renders the marker in the %s state", (_name, child) => {
    render(<SimulationsLayout>{child}</SimulationsLayout>);
    expect(screen.getByTestId("sim-banner-status")).toBeInTheDocument();
    expect(
      screen.getByText(/Simulation — this is not live data/),
    ).toBeInTheDocument();
  });

  it("shows a pending status until a route reports lifecycle, never a false Active", () => {
    render(
      <SimulationsLayout>
        <div>Loading playback…</div>
      </SimulationsLayout>,
    );
    const pill = screen.getByTestId("sim-banner-status");
    expect(pill.getAttribute("data-status")).toBe("unknown");
    expect(pill.getAttribute("aria-label")).toContain("pending");
  });

  it("reflects the tenant lifecycle published by the route", async () => {
    render(
      <SimulationsLayout>
        <Reporter status="Archived" />
      </SimulationsLayout>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("sim-banner-status").getAttribute("data-status"),
      ).toBe("archived"),
    );
  });

  it("keeps the marker non-dismissible (no close control)", () => {
    render(
      <SimulationsLayout>
        <Reporter status="Active" />
      </SimulationsLayout>,
    );
    expect(screen.queryByRole("button", { name: /dismiss|close/i })).toBeNull();
  });

  it("maps API tenant statuses onto lifecycle states", () => {
    expect(toLifecycleStatus("Active")).toBe("active");
    expect(toLifecycleStatus("Paused")).toBe("paused");
    expect(toLifecycleStatus("Archiving")).toBe("archived");
    expect(toLifecycleStatus("Archived")).toBe("archived");
    expect(toLifecycleStatus("Completed")).toBe("completed");
    expect(toLifecycleStatus(null)).toBe("unknown");
    expect(toLifecycleStatus("something-else")).toBe("unknown");
  });
});
