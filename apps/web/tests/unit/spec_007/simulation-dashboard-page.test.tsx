/**
 * AUD-015 / AUD-016 — the simulation dashboard must refresh shared exercise
 * activity within five seconds, display the throttle notice, state the cache
 * key situation truthfully, link a completed report by `exercise_report_id`,
 * and surface assignment-backed personas.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import {
  SIMULATION_REFRESH_INTERVAL_MS,
} from "@/lib/simulation-refresh";

const getSimulation = vi.fn();
const getPlaybackEvents = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ tenantId: "sim-1" }),
}));

vi.mock("@/lib/api/simulations", () => ({
  getSimulation: (...args: unknown[]) => getSimulation(...args),
  pauseSimulation: vi.fn(),
  resumeSimulation: vi.fn(),
  archiveSimulation: vi.fn(),
}));

vi.mock("@/lib/api/simulation-playback", () => ({
  getPlaybackEvents: (...args: unknown[]) => getPlaybackEvents(...args),
  recordEventLogEntry: vi.fn(),
}));

vi.mock("@/components/simulation-chat-pane", () => ({
  SimulationChatPane: () => <div data-testid="chat-pane" />,
}));
vi.mock("@/components/simulation-map", () => ({
  SimulationMap: () => <div data-testid="sim-map" />,
}));
vi.mock("@/components/simulation-server-clock", () => ({
  SimulationServerClock: () => <div data-testid="sim-clock" />,
}));
vi.mock("@/components/simulation-warp-controls", () => ({
  SimulationWarpControls: () => <div data-testid="sim-warp" />,
}));
vi.mock("@/components/simulation-persona-workspace", () => ({
  SimulationPersonaWorkspace: (props: {
    assignments: unknown[];
    unassignedParticipants: string[];
  }) => (
    <div
      data-testid="persona-workspace-stub"
      data-assignments={String(props.assignments.length)}
      data-unassigned={String(props.unassignedParticipants.length)}
    />
  ),
}));

import SimulationDashboardPage from "@/app/simulations/[tenantId]/page";

function detail(overrides: Record<string, unknown> = {}) {
  return {
    tenant_id: "sim-1",
    scenario_id: "sc-1",
    scenario_run_id: "run-1",
    scenario_type: "Bushfire",
    status: "Active",
    created_by: "oid-creator",
    created_at: "2026-01-01T00:00:00Z",
    ttl_hours: 72,
    expires_at: "2026-01-04T00:00:00Z",
    participants: ["oid-a", "oid-b"],
    participant_assignments: [
      {
        oid: "oid-a",
        persona_id: "incident-commander",
        organisation_id: "org-1",
        jurisdiction_id: "nsw",
        role: "coordinator",
      },
    ],
    jurisdictions: ["NSW"],
    resource_limits: { max_signals: 100, max_recommendations: 10, max_duration_hours: 48 },
    resource_consumption: {
      signal_count: 1,
      recommendation_count: 0,
      storage_bytes: 2048,
      cache_keys: 0,
    },
    throttle_mode: "normal",
    throttle_quota_pct: 100,
    elapsed_seconds: 0,
    ...overrides,
  };
}

describe("SimulationDashboardPage", () => {
  beforeEach(() => {
    getSimulation.mockReset();
    getPlaybackEvents.mockReset();
    getPlaybackEvents.mockResolvedValue({ events: [] });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("refreshes shared exercise activity at most every five seconds", () => {
    expect(SIMULATION_REFRESH_INTERVAL_MS).toBeLessThanOrEqual(5000);
  });

  it("polls persisted events on the five-second cadence", async () => {
    vi.useFakeTimers();
    getSimulation.mockResolvedValue(detail());
    render(<SimulationDashboardPage />);

    await vi.waitFor(() => expect(getPlaybackEvents).toHaveBeenCalledTimes(1));
    await vi.advanceTimersByTimeAsync(SIMULATION_REFRESH_INTERVAL_MS);
    expect(getPlaybackEvents).toHaveBeenCalledTimes(2);
  });

  it("shows the throttle notice supplied by the API", async () => {
    getSimulation.mockResolvedValue(
      detail({
        throttle_mode: "incident-throttled",
        throttle_quota_pct: 25,
        throttle_notice: "Live incident declared — simulation quota reduced to 25%.",
      }),
    );
    render(<SimulationDashboardPage />);

    expect(await screen.findByTestId("sim-throttle-notice")).toHaveTextContent(
      /quota reduced to 25%/,
    );
    expect(screen.getByTestId("sim-throttle-status")).toHaveTextContent(
      /incident-throttled · 25% quota/,
    );
  });

  it("omits the throttle notice when the API reports none", async () => {
    getSimulation.mockResolvedValue(detail());
    render(<SimulationDashboardPage />);
    await screen.findByTestId("sim-cache-keys");
    expect(screen.queryByTestId("sim-throttle-notice")).toBeNull();
  });

  it("never presents an unmeasured cache-key count as a measured zero", async () => {
    getSimulation.mockResolvedValue(detail());
    render(<SimulationDashboardPage />);
    expect(await screen.findByTestId("sim-cache-keys")).toHaveTextContent("None reported");
  });

  it("states cache keys are unavailable when the API omits the field", async () => {
    getSimulation.mockResolvedValue(
      detail({
        resource_consumption: { signal_count: 1, recommendation_count: 0, storage_bytes: 0 },
      }),
    );
    render(<SimulationDashboardPage />);
    expect(await screen.findByTestId("sim-cache-keys")).toHaveTextContent("Not reported");
  });

  it("renders a measured cache-key count when one is reported", async () => {
    getSimulation.mockResolvedValue(
      detail({
        resource_consumption: {
          signal_count: 1,
          recommendation_count: 0,
          storage_bytes: 0,
          cache_keys: 12,
        },
      }),
    );
    render(<SimulationDashboardPage />);
    expect(await screen.findByTestId("sim-cache-keys")).toHaveTextContent("12");
  });

  it("links a completed report by exercise_report_id, not tenant id", async () => {
    getSimulation.mockResolvedValue(
      detail({ status: "Archived", exercise_report_id: "rpt-42" }),
    );
    render(<SimulationDashboardPage />);

    const link = await screen.findByTestId("sim-report-link");
    expect(link).toHaveAttribute("href", "/simulations/reports/rpt-42");
    expect(screen.queryByTestId("sim-report-pending")).toBeNull();
  });

  it("says the report is not available yet rather than linking the tenant id", async () => {
    getSimulation.mockResolvedValue(detail({ status: "Archived" }));
    render(<SimulationDashboardPage />);

    expect(await screen.findByTestId("sim-report-pending")).toBeInTheDocument();
    expect(screen.queryByTestId("sim-report-link")).toBeNull();
  });

  it("passes assignments and unassigned participants to the workspace panel", async () => {
    getSimulation.mockResolvedValue(detail());
    render(<SimulationDashboardPage />);

    await waitFor(() => {
      const stub = screen.getByTestId("persona-workspace-stub");
      expect(stub).toHaveAttribute("data-assignments", "1");
      expect(stub).toHaveAttribute("data-unassigned", "1");
    });
  });
});
