/**
 * AUD-016 — create must expose scenario-template / replay choice and send
 * structured participant assignments instead of an empty list.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const createSimulation = vi.fn();
const seedSimulation = vi.fn();
const seedReplay = vi.fn();
const addParticipants = vi.fn();
const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/lib/api/simulations", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/simulations")>(
    "@/lib/api/simulations",
  );
  return {
    ALLOWED_WARP_SPEEDS: actual.ALLOWED_WARP_SPEEDS,
    SCENARIO_TEMPLATES: actual.SCENARIO_TEMPLATES,
    createSimulation: (...args: unknown[]) => createSimulation(...args),
    seedSimulation: (...args: unknown[]) => seedSimulation(...args),
    seedReplay: (...args: unknown[]) => seedReplay(...args),
    addParticipants: (...args: unknown[]) => addParticipants(...args),
  };
});

import CreateSimulationPage from "@/app/simulations/create/page";

describe("CreateSimulationPage", () => {
  beforeEach(() => {
    createSimulation.mockReset().mockResolvedValue({ tenant_id: "tenant-1" });
    seedSimulation.mockReset().mockResolvedValue({ status: "accepted" });
    seedReplay.mockReset().mockResolvedValue({ status: "accepted" });
    addParticipants.mockReset().mockResolvedValue({ tenant_id: "tenant-1", participants: [] });
    push.mockReset();
  });

  const submit = () =>
    fireEvent.click(screen.getByRole("button", { name: /create simulation/i }));

  it("offers template and replay seeding choices", () => {
    render(<CreateSimulationPage />);
    const group = screen.getByTestId("seed-source");
    expect(group).toHaveTextContent(/curated scenario template/i);
    expect(group).toHaveTextContent(/historical incident window/i);
  });

  it("creates with a scenario template and seeds it", async () => {
    render(<CreateSimulationPage />);
    fireEvent.click(screen.getByLabelText(/curated scenario template/i));
    fireEvent.change(screen.getByLabelText(/^Scenario template$/), {
      target: { value: "nsw-flood-riverine" },
    });
    submit();

    await waitFor(() => expect(push).toHaveBeenCalledWith("/simulations/tenant-1"));
    expect(createSimulation).toHaveBeenCalledWith(
      expect.objectContaining({ scenario_template_id: "nsw-flood-riverine" }),
    );
    expect(seedSimulation).toHaveBeenCalledWith("tenant-1", "nsw-flood-riverine");
    expect(seedReplay).not.toHaveBeenCalled();
  });

  it("creates with a historical replay window", async () => {
    render(<CreateSimulationPage />);
    fireEvent.click(screen.getByLabelText(/historical incident window/i));
    fireEvent.change(screen.getByLabelText(/source incident id/i), {
      target: { value: "incident-77" },
    });
    fireEvent.change(screen.getByLabelText(/window start/i), {
      target: { value: "2026-01-01T00:00" },
    });
    fireEvent.change(screen.getByLabelText(/window end/i), {
      target: { value: "2026-01-02T00:00" },
    });
    submit();

    await waitFor(() =>
      expect(seedReplay).toHaveBeenCalledWith(
        "tenant-1",
        "incident-77",
        "2026-01-01T00:00",
        "2026-01-02T00:00",
      ),
    );
    expect(createSimulation).toHaveBeenCalledWith(
      expect.not.objectContaining({ scenario_template_id: expect.anything() }),
    );
  });

  it("posts structured participant assignments", async () => {
    render(<CreateSimulationPage />);
    fireEvent.click(screen.getByRole("button", { name: /add participant/i }));
    fireEvent.change(screen.getByLabelText(/participant object id/i), {
      target: { value: "oid-9" },
    });
    fireEvent.change(screen.getByLabelText(/participant persona/i), {
      target: { value: "incident-controller" },
    });
    fireEvent.change(screen.getByLabelText(/participant organisation/i), {
      target: { value: "nsw-rfs" },
    });
    fireEvent.change(screen.getByLabelText(/participant jurisdiction/i), {
      target: { value: "nsw" },
    });
    submit();

    await waitFor(() =>
      expect(addParticipants).toHaveBeenCalledWith("tenant-1", [
        {
          oid: "oid-9",
          persona: "incident-controller",
          organisation_id: "nsw-rfs",
          jurisdiction_id: "nsw",
          role: "participant",
        },
      ]),
    );
  });

  it("reports a partial failure instead of silently navigating away", async () => {
    addParticipants.mockRejectedValue(new Error("API 403: not coordinator"));
    render(<CreateSimulationPage />);
    fireEvent.click(screen.getByRole("button", { name: /add participant/i }));
    fireEvent.change(screen.getByLabelText(/participant object id/i), {
      target: { value: "oid-9" },
    });
    submit();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/tenant-1 was created/i);
    expect(alert).toHaveTextContent(/API 403: not coordinator/);
    expect(push).not.toHaveBeenCalled();
  });
});
