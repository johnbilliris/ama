/**
 * AUD-021 — the report deep link must resolve by report identity, must tell
 * 403 / 404 / pending apart, and must render the escalated, timed-out and
 * prior-run comparison fields.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

const getReportById = vi.fn();

const { TestSimulationApiError } = vi.hoisted(() => {
  class TestSimulationApiError extends Error {
    status: number;
    body: string;
    constructor(status: number, body: string) {
      super(`API ${status}: ${body}`);
      this.name = "SimulationApiError";
      this.status = status;
      this.body = body;
    }
  }
  return { TestSimulationApiError };
});

vi.mock("next/navigation", () => ({
  useParams: () => ({ reportId: "rpt-42" }),
}));

vi.mock("@/lib/api/simulations", () => ({
  getReportById: (...args: unknown[]) => getReportById(...args),
  SimulationApiError: TestSimulationApiError,
}));

vi.mock("@/components/simulation-lifecycle", () => ({
  useReportSimulationLifecycle: () => undefined,
}));

import ExerciseReportPage from "@/app/simulations/reports/[reportId]/page";

function report(overrides: Record<string, unknown> = {}) {
  return {
    report_id: "rpt-42",
    tenant_id: "sim-1",
    scenario_type: "Bushfire",
    generated_at: "2026-01-02T00:00:00Z",
    exercise_timeline: [
      { event_type: "state_change", wall_clock_time: "2026-01-01T01:00:00Z", payload: {} },
    ],
    participating_organisations: ["org-1"],
    participating_personas: ["incident-commander"],
    signal_summary: { total: 3, by_category: { fire: 3 }, by_source: {} },
    recommendation_summary: {
      total: 5,
      approved: 1,
      rejected: 1,
      escalated: 2,
      timed_out: 1,
      pending: 0,
    },
    alert_summary: { total: 1, published: 0, blocked_simulation: 1 },
    coordination_gaps: [],
    performance_metrics: {
      time_to_first_recommendation_s: null,
      time_to_alert_publication_s: null,
      coordination_coverage_pct: null,
    },
    benchmark_comparison: [
      {
        metric: "time_to_first_recommendation_s",
        target: 120,
        actual: 90,
        passed: true,
        prior_actual: 150,
        delta_from_prior: -60,
      },
    ],
    ...overrides,
  };
}

describe("ExerciseReportPage", () => {
  beforeEach(() => {
    getReportById.mockReset();
  });

  it("requests the report by report identity", async () => {
    getReportById.mockResolvedValue(report());
    render(<ExerciseReportPage />);
    await screen.findByText(/Exercise Report/);
    expect(getReportById).toHaveBeenCalledWith("rpt-42");
  });

  it("renders escalated and timed-out decision outcomes", async () => {
    getReportById.mockResolvedValue(report());
    render(<ExerciseReportPage />);

    const card = await screen.findByTestId("report-recommendation-summary");
    expect(card).toHaveTextContent("Escalated");
    expect(card).toHaveTextContent("Timed out");
  });

  it("renders the prior-run comparison columns", async () => {
    getReportById.mockResolvedValue(report());
    render(<ExerciseReportPage />);

    const section = await screen.findByTestId("report-benchmark-comparison");
    expect(section).toHaveTextContent("Prior");
    expect(section).toHaveTextContent("150");
    expect(section).toHaveTextContent("-60");
  });

  it("says so explicitly when there is no prior exercise", async () => {
    getReportById.mockResolvedValue(
      report({
        benchmark_comparison: [
          {
            metric: "coordination_coverage_pct",
            target: 80,
            actual: null,
            passed: false,
            prior_actual: null,
            delta_from_prior: null,
          },
        ],
      }),
    );
    render(<ExerciseReportPage />);
    expect(await screen.findByTestId("report-benchmark-comparison")).toHaveTextContent(
      "No prior exercise",
    );
  });

  it("distinguishes a forbidden report from a missing one and from pending generation", async () => {
    getReportById.mockRejectedValue(new TestSimulationApiError(403, "not a participant"));
    const forbidden = render(<ExerciseReportPage />);
    expect(await screen.findByTestId("report-error-forbidden")).toBeInTheDocument();
    forbidden.unmount();

    getReportById.mockRejectedValue(new TestSimulationApiError(404, "Exercise report not found"));
    const missing = render(<ExerciseReportPage />);
    expect(await screen.findByTestId("report-error-not-found")).toBeInTheDocument();
    missing.unmount();

    getReportById.mockRejectedValue(
      new TestSimulationApiError(409, "Cannot generate report while simulation is active"),
    );
    const pending = render(<ExerciseReportPage />);
    expect(await screen.findByTestId("report-error-pending")).toBeInTheDocument();
    pending.unmount();

    getReportById.mockRejectedValue(new Error("network down"));
    render(<ExerciseReportPage />);
    expect(await screen.findByTestId("report-error-unknown")).toHaveTextContent("network down");
  });
});
