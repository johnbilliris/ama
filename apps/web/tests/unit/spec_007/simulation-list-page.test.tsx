/**
 * AUD-016 — simulation list page must surface load failures (not swallow
 * them) and provide working pagination.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const listSimulations = vi.fn();
const pauseSimulation = vi.fn();

vi.mock("@/lib/api/simulations", () => ({
  listSimulations: (...args: unknown[]) => listSimulations(...args),
  pauseSimulation: (...args: unknown[]) => pauseSimulation(...args),
  resumeSimulation: vi.fn(),
  archiveSimulation: vi.fn(),
  deleteSimulation: vi.fn(),
}));

import SimulationListPage from "@/app/simulations/page";

function summary(id: string, status = "Active") {
  return {
    tenant_id: id,
    scenario_type: "Bushfire",
    status,
    created_at: "2026-01-01T00:00:00Z",
    participant_count: 2,
    signal_count: 5,
    storage_bytes: 2048,
    current_warp_speed: 1,
  };
}

describe("SimulationListPage", () => {
  beforeEach(() => {
    listSimulations.mockReset();
    pauseSimulation.mockReset();
  });

  it("renders a retryable error instead of an empty list when loading fails", async () => {
    listSimulations.mockRejectedValue(new Error("API 403: forbidden"));
    render(<SimulationListPage />);

    const alert = await screen.findByTestId("sim-list-error");
    expect(alert).toHaveTextContent(/API 403: forbidden/);
    expect(screen.queryByText(/No simulation exercises found/)).toBeNull();

    listSimulations.mockResolvedValue({
      simulations: [summary("t-1")],
      total: 1,
      limit: 20,
      offset: 0,
    });
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    await waitFor(() => expect(screen.queryByTestId("sim-list-error")).toBeNull());
  });

  it("paginates with real limit/offset requests and reports the visible range", async () => {
    const firstPage = Array.from({ length: 20 }, (_, i) => summary(`t-${i}`));
    listSimulations.mockImplementation(async (_status, _limit, offset) => ({
      simulations: offset === 0 ? firstPage : [summary("t-20")],
      total: 21,
      limit: 20,
      offset: offset ?? 0,
    }));

    render(<SimulationListPage />);
    await waitFor(() =>
      expect(screen.getByTestId("sim-page-range")).toHaveTextContent("1–20 of 21"),
    );
    expect(screen.getByTestId("sim-page-prev")).toBeDisabled();

    fireEvent.click(screen.getByTestId("sim-page-next"));
    await waitFor(() =>
      expect(screen.getByTestId("sim-page-range")).toHaveTextContent("21–21 of 21"),
    );
    expect(listSimulations).toHaveBeenLastCalledWith(undefined, 20, 20);
    expect(screen.getByTestId("sim-page-next")).toBeDisabled();
    expect(screen.getByTestId("sim-page-prev")).toBeEnabled();
  });

  it("surfaces lifecycle action failures", async () => {
    listSimulations.mockResolvedValue({
      simulations: [summary("t-1")],
      total: 1,
      limit: 20,
      offset: 0,
    });
    pauseSimulation.mockRejectedValue(new Error("API 409: not active"));

    render(<SimulationListPage />);
    fireEvent.click(await screen.findByRole("button", { name: /pause/i }));

    expect(await screen.findByTestId("sim-action-error")).toHaveTextContent(
      /API 409: not active/,
    );
  });
});
