"use client";

/**
 * AUD-015 / AUD-016 — assignment-backed persona workspace inside the exercise.
 *
 * The tenant response already carries `participant_assignments`, and
 * `GET /api/personas/{personaId}/workspace` already resolves the simulation
 * tenant from the request context and refuses a persona the caller is not
 * assigned to. This panel joins the two so an exercise participant can see
 * their own tenant-scoped tasks and pending approvals without leaving the
 * simulation shell.
 *
 * In explicitly configured dev access, any listed persona can be selected.
 */
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";

import { simulationPrincipalOid } from "@/lib/api/simulation-auth";
import {
  getPersonaWorkspace,
  PersonaWorkspaceError,
  type PersonaWorkspacePayload,
} from "@/lib/api/personas";
import type { SimulationParticipantAssignment } from "@/lib/api/simulations";
import { SIMULATION_REFRESH_INTERVAL_MS } from "@/lib/simulation-refresh";

/** Shared with the event log: collaborative state must refresh within 5s (US3-AS4). */
export const WORKSPACE_REFRESH_INTERVAL_MS = SIMULATION_REFRESH_INTERVAL_MS;

interface Props {
  assignments: SimulationParticipantAssignment[];
  /** OIDs with no recorded persona assignment. */
  unassignedParticipants: string[];
  tenantId?: string;
}

function isAnonymousDevAccessEnabled(): boolean {
  return process.env.NEXT_PUBLIC_ALLOW_ANONYMOUS_DEV_ACCESS === "1";
}

type LoadState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; payload: PersonaWorkspacePayload }
  | { kind: "error"; status: number; message: string };

function describeError(status: number, message: string): string {
  switch (status) {
    case 403:
      return "Your account is not assigned to this persona in this exercise.";
    case 404:
      return "No workspace exists for that persona and incident in this exercise.";
    case 0:
      return `Workspace request failed: ${message}`;
    default:
      return message;
  }
}

export function SimulationPersonaWorkspace({ assignments, unassignedParticipants, tenantId }: Props) {
  const anonymousDevAccess = isAnonymousDevAccessEnabled();
  const [oid, setOid] = useState<string | null>(null);
  const [oidResolved, setOidResolved] = useState(false);
  const [selectedDevAssignmentOid, setSelectedDevAssignmentOid] = useState("");
  const [incidentId, setIncidentId] = useState("");
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null);
  const [state, setState] = useState<LoadState>({ kind: "idle" });

  useEffect(() => {
    let cancelled = false;
    void simulationPrincipalOid().then((value) => {
      if (cancelled) return;
      setOid(value);
      setOidResolved(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const myAssignment = useMemo(() => {
    if (anonymousDevAccess) {
      return (
        assignments.find((assignment) => assignment.oid === selectedDevAssignmentOid) ??
        assignments[0] ??
        null
      );
    }
    return oid ? assignments.find((assignment) => assignment.oid === oid) ?? null : null;
  }, [assignments, anonymousDevAccess, oid, selectedDevAssignmentOid]);
  const personaId = myAssignment?.persona_id ?? null;

  const load = useCallback(
    async (incident: string, silent = false) => {
      if (!personaId) return;
      if (!silent) setState({ kind: "loading" });
      try {
        const payload = tenantId
          ? await getPersonaWorkspace(personaId, incident, tenantId)
          : await getPersonaWorkspace(personaId, incident);
        setState({ kind: "ready", payload });
      } catch (err) {
        if (err instanceof PersonaWorkspaceError) {
          setState({ kind: "error", status: err.status, message: err.message });
        } else {
          setState({
            kind: "error",
            status: 0,
            message: err instanceof Error ? err.message : String(err),
          });
        }
      }
    },
    [personaId, tenantId],
  );

  useEffect(() => {
    if (!activeIncidentId || !personaId) return;
    const id = setInterval(
      () => void load(activeIncidentId, true),
      WORKSPACE_REFRESH_INTERVAL_MS,
    );
    return () => clearInterval(id);
  }, [activeIncidentId, personaId, load]);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    const incident = incidentId.trim();
    if (!incident) return;
    setActiveIncidentId(incident);
    void load(incident);
  };

  return (
    <section className="sim-panel-section" data-testid="sim-persona-workspace">
      <header className="sim-panel-header">
        <h2>Assigned personas ({assignments.length})</h2>
      </header>

      {assignments.length === 0 ? (
        <p className="sim-panel-empty">No persona assignments recorded for this exercise.</p>
      ) : (
        <ul className="sim-participant-list" data-testid="sim-assignment-list">
          {assignments.map((assignment) => (
            <li key={assignment.oid} title={assignment.oid}>
              <strong>{assignment.persona_id ?? "No persona"}</strong>
              {" · "}
              {assignment.role ?? "participant"}
              {" · "}
              {assignment.organisation_id ?? "no organisation"}
              {" · "}
              {assignment.jurisdiction_id ?? "no jurisdiction"}
              {(anonymousDevAccess ? assignment === myAssignment : assignment.oid === oid) && (
                <span data-testid="sim-assignment-self"> (you)</span>
              )}
            </li>
          ))}
        </ul>
      )}

      {anonymousDevAccess && assignments.length > 0 && (
        <>
          <label htmlFor="sim-dev-persona">Developer persona</label>
          <select
            id="sim-dev-persona"
            value={myAssignment?.oid ?? ""}
            onChange={(event) => setSelectedDevAssignmentOid(event.target.value)}
          >
            {assignments.map((assignment) => (
              <option key={assignment.oid} value={assignment.oid}>
                {assignment.persona_id ?? "Unassigned persona"}
              </option>
            ))}
          </select>
        </>
      )}

      {unassignedParticipants.length > 0 && (
        <>
          <p className="sim-panel-empty" data-testid="sim-unassigned-participants">
            {unassignedParticipants.length} participant(s) have no persona assignment recorded.
          </p>
          <ul className="sim-participant-list">
            {unassignedParticipants.map((oidValue) => (
              <li key={oidValue} title={oidValue}>
                {oidValue}
              </li>
            ))}
          </ul>
        </>
      )}

      {!oidResolved && <p className="sim-panel-empty">Resolving your exercise identity…</p>}

      {oidResolved && !oid && !anonymousDevAccess && (
        <p className="sim-panel-empty" data-testid="sim-workspace-signin">
          Sign in to load your assigned-persona workspace.
        </p>
      )}

      {oidResolved && oid && !personaId && (
        <p className="sim-panel-empty" data-testid="sim-workspace-unassigned">
          Your account has no persona assignment in this exercise, so no
          assignment-scoped workspace can be loaded.
        </p>
      )}

      {personaId && (
        <form className="sim-workspace-form" onSubmit={onSubmit}>
          <label htmlFor="sim-workspace-incident">Incident ID</label>
          <input
            id="sim-workspace-incident"
            name="incidentId"
            value={incidentId}
            onChange={(e) => setIncidentId(e.target.value)}
            placeholder="siminc-…"
          />
          <button type="submit" disabled={!incidentId.trim()}>
            Load {personaId} workspace
          </button>
        </form>
      )}

      {state.kind === "loading" && <p className="sim-panel-empty">Loading workspace…</p>}

      {state.kind === "error" && (
        <p
          role="alert"
          data-testid="sim-workspace-error"
          data-status={state.status}
          className="sim-panel-empty"
        >
          {describeError(state.status, state.message)}
        </p>
      )}

      {state.kind === "ready" && (
        <div data-testid="sim-workspace-result">
          <h3>Pending approvals ({state.payload.pendingApprovals?.length ?? 0})</h3>
          {(state.payload.pendingApprovals?.length ?? 0) === 0 ? (
            <p className="sim-panel-empty">No approvals awaiting this persona.</p>
          ) : (
            <ul data-testid="sim-workspace-approvals">
              {state.payload.pendingApprovals!.map((approval, index) => (
                <li key={String(approval.recommendation_id ?? index)}>
                  {String(approval.recommendation_id ?? "recommendation")} ·{" "}
                  {String(approval.status ?? "pending")}
                </li>
              ))}
            </ul>
          )}

          <h3>Tasks ({state.payload.tasks.length})</h3>
          {state.payload.tasks.length === 0 ? (
            <p className="sim-panel-empty">No tasks assigned.</p>
          ) : (
            <ul data-testid="sim-workspace-tasks">
              {state.payload.tasks.map((task) => (
                <li key={task.task_id}>
                  {task.title} · {task.status}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
