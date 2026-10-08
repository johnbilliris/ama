/**
 * AUD-015 — the exercise must expose persona assignments and the
 * assignment-backed workspace (tasks + pending approvals); only the explicit
 * dev-access mode may use a synthetic identity.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

const simulationPrincipalOid = vi.fn();
const getPersonaWorkspace = vi.fn();

vi.mock("@/lib/api/simulation-auth", () => ({
  simulationPrincipalOid: () => simulationPrincipalOid(),
}));

const { TestPersonaWorkspaceError } = vi.hoisted(() => {
  class TestPersonaWorkspaceError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.name = "PersonaWorkspaceError";
      this.status = status;
    }
  }
  return { TestPersonaWorkspaceError };
});

vi.mock("@/lib/api/personas", () => ({
  getPersonaWorkspace: (...args: unknown[]) => getPersonaWorkspace(...args),
  PersonaWorkspaceError: TestPersonaWorkspaceError,
}));

import {
  SimulationPersonaWorkspace,
  WORKSPACE_REFRESH_INTERVAL_MS,
} from "@/components/simulation-persona-workspace";

const ASSIGNMENTS = [
  {
    oid: "oid-a",
    persona_id: "incident-commander",
    organisation_id: "org-1",
    jurisdiction_id: "nsw",
    role: "coordinator",
  },
  {
    oid: "oid-b",
    persona_id: "operations-officer",
    organisation_id: "org-2",
    jurisdiction_id: "vic",
    role: "participant",
  },
];

function workspacePayload() {
  return {
    persona: {
      persona_id: "incident-commander",
      display_name: "Incident Commander",
      organisation_id: "org-1",
      jurisdiction_id: "nsw",
      role: "coordinator",
    },
    tasks: [{ task_id: "task-1", title: "Stage strike team", status: "in_progress", priority: "high" }],
    dependencies: [],
    pendingApprovals: [{ recommendation_id: "rec-1", status: "escalated" }],
    inboundRequests: [],
  };
}

async function loadWorkspace() {
  fireEvent.change(await screen.findByLabelText(/incident id/i), {
    target: { value: "siminc-1" },
  });
  fireEvent.click(screen.getByRole("button", { name: /load incident-commander workspace/i }));
}

describe("SimulationPersonaWorkspace", () => {
  beforeEach(() => {
    simulationPrincipalOid.mockReset();
    getPersonaWorkspace.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllEnvs();
  });

  it("refreshes collaborative state at most every five seconds", () => {
    expect(WORKSPACE_REFRESH_INTERVAL_MS).toBeLessThanOrEqual(5000);
  });

  it("renders the persona/organisation/jurisdiction of each assignment", async () => {
    simulationPrincipalOid.mockResolvedValue(null);
    render(
      <SimulationPersonaWorkspace assignments={ASSIGNMENTS} unassignedParticipants={["oid-c"]} />,
    );

    const list = await screen.findByTestId("sim-assignment-list");
    expect(list).toHaveTextContent("incident-commander");
    expect(list).toHaveTextContent("org-1");
    expect(list).toHaveTextContent("nsw");
    expect(list).toHaveTextContent("operations-officer");
    expect(screen.getByTestId("sim-unassigned-participants")).toHaveTextContent("1 participant");
  });

  it("withholds the workspace instead of guessing an identity when sign-in is unavailable", async () => {
    vi.stubEnv("NEXT_PUBLIC_ALLOW_ANONYMOUS_DEV_ACCESS", "0");
    simulationPrincipalOid.mockResolvedValue(null);
    render(<SimulationPersonaWorkspace assignments={ASSIGNMENTS} unassignedParticipants={[]} />);

    expect(await screen.findByTestId("sim-workspace-signin")).toBeInTheDocument();
    expect(screen.queryByLabelText(/incident id/i)).toBeNull();
    expect(getPersonaWorkspace).not.toHaveBeenCalled();
  });

  it("lets an unauthenticated dev user select and load any assigned persona workspace", async () => {
    vi.stubEnv("NEXT_PUBLIC_ALLOW_ANONYMOUS_DEV_ACCESS", "1");
    simulationPrincipalOid.mockResolvedValue("dev-user");
    getPersonaWorkspace.mockResolvedValue(workspacePayload());
    render(<SimulationPersonaWorkspace assignments={ASSIGNMENTS} unassignedParticipants={[]} tenantId="sim-1" />);

    const selector = await screen.findByLabelText(/developer persona/i);
    expect(selector).toHaveValue("oid-a");
    fireEvent.change(selector, { target: { value: "oid-b" } });
    fireEvent.change(screen.getByLabelText(/incident id/i), { target: { value: "siminc-1" } });
    fireEvent.click(screen.getByRole("button", { name: /load operations-officer workspace/i }));

    await waitFor(() =>
      expect(getPersonaWorkspace).toHaveBeenCalledWith("operations-officer", "siminc-1", "sim-1"),
    );
  });

  it("explains when the signed-in account has no assignment", async () => {
    simulationPrincipalOid.mockResolvedValue("oid-zzz");
    render(<SimulationPersonaWorkspace assignments={ASSIGNMENTS} unassignedParticipants={[]} />);

    expect(await screen.findByTestId("sim-workspace-unassigned")).toBeInTheDocument();
    expect(screen.queryByLabelText(/incident id/i)).toBeNull();
  });

  it("loads the assigned persona's pending approvals and tasks", async () => {
    simulationPrincipalOid.mockResolvedValue("oid-a");
    getPersonaWorkspace.mockResolvedValue(workspacePayload());
    render(<SimulationPersonaWorkspace assignments={ASSIGNMENTS} unassignedParticipants={[]} />);

    expect(await screen.findByTestId("sim-assignment-self")).toBeInTheDocument();
    await loadWorkspace();

    await waitFor(() =>
      expect(screen.getByTestId("sim-workspace-approvals")).toHaveTextContent("rec-1"),
    );
    expect(screen.getByTestId("sim-workspace-approvals")).toHaveTextContent("escalated");
    expect(screen.getByTestId("sim-workspace-tasks")).toHaveTextContent("Stage strike team");
    expect(getPersonaWorkspace).toHaveBeenCalledWith("incident-commander", "siminc-1");
  });

  it("distinguishes a forbidden assignment from a missing workspace", async () => {
    simulationPrincipalOid.mockResolvedValue("oid-a");
    getPersonaWorkspace.mockRejectedValue(
      new TestPersonaWorkspaceError("Simulation persona assignment required", 403),
    );
    render(<SimulationPersonaWorkspace assignments={ASSIGNMENTS} unassignedParticipants={[]} />);
    await loadWorkspace();

    const alert = await screen.findByTestId("sim-workspace-error");
    expect(alert).toHaveAttribute("data-status", "403");
    expect(alert).toHaveTextContent(/not assigned to this persona/i);

    getPersonaWorkspace.mockRejectedValue(new TestPersonaWorkspaceError("missing", 404));
    fireEvent.click(screen.getByRole("button", { name: /load incident-commander workspace/i }));
    await waitFor(() =>
      expect(screen.getByTestId("sim-workspace-error")).toHaveAttribute("data-status", "404"),
    );
  });

  it("re-reads the workspace on the five-second cadence once loaded", async () => {
    vi.useFakeTimers();
    simulationPrincipalOid.mockResolvedValue("oid-a");
    getPersonaWorkspace.mockResolvedValue(workspacePayload());
    render(<SimulationPersonaWorkspace assignments={ASSIGNMENTS} unassignedParticipants={[]} />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    fireEvent.change(screen.getByLabelText(/incident id/i), {
      target: { value: "siminc-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /load incident-commander workspace/i }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(getPersonaWorkspace).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(WORKSPACE_REFRESH_INTERVAL_MS);
    });
    expect(getPersonaWorkspace).toHaveBeenCalledTimes(2);
  });
});
