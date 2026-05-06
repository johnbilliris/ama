import type { PersonaWorkspacePayload } from "../../lib/api/personas";
import { TaskStatusPanel } from "./task-status-panel";
import FieldCoordinatorOffline from "../../app/workspaces/[personaId]/_panels/field-coordinator-offline";
import IcApprovalCard from "../../app/workspaces/[personaId]/_panels/ic-approval-card";
import ObserverAuditorTimeline from "../../app/workspaces/[personaId]/_panels/observer-auditor-timeline";
import PioAwsComposer from "../../app/workspaces/[personaId]/_panels/pio-aws-composer";
import PlanningIapComposer from "../../app/workspaces/[personaId]/_panels/planning-iap-composer";
import ResilienceHandoverPdf from "../../app/workspaces/[personaId]/_panels/resilience-handover-pdf";
import RiskMatrix from "../../app/workspaces/[personaId]/_panels/risk-matrix";
import SpanOfControlWarning from "../../app/workspaces/[personaId]/_panels/span-of-control-warning";

interface PersonaWorkspaceProps {
  workspace: PersonaWorkspacePayload;
}

export function PersonaWorkspace({ workspace }: PersonaWorkspaceProps) {
  const primaryTask = workspace.tasks[0];
  const role = workspace.persona.role;
  const scenarioId = primaryTask?.task_id ?? "0";

  return (
    <section className="workspace-shell">
      <header className="workspace-header">
        <p className="workspace-kicker">{workspace.persona.role}</p>
        <h1 className="workspace-title">{workspace.persona.display_name}</h1>
        <p className="workspace-org">{workspace.persona.organisation_id}</p>
      </header>

      <div className="workspace-columns">
        <article className="workspace-panel">
          <h2 className="workspace-panel-title">Assigned tasks</h2>
          <ul className="workspace-list">
            {workspace.tasks.map((task) => (
              <li key={task.task_id} className="workspace-list-item">
                <strong>{task.title}</strong>
                <div className="workspace-meta">
                  {task.priority} priority · {task.status}
                </div>
              </li>
            ))}
          </ul>
        </article>

        <article className="workspace-panel">
          <h2 className="workspace-panel-title">Dependencies</h2>
          <ul className="workspace-list">
            {workspace.dependencies.length === 0 ? (
              <li className="workspace-list-item">No visible external dependencies.</li>
            ) : (
              workspace.dependencies.map((task) => (
                <li key={task.task_id} className="workspace-list-item">
                  <strong>{task.title}</strong>
                  <div className="workspace-meta">{task.status}</div>
                </li>
              ))
            )}
          </ul>
        </article>
      </div>

      {primaryTask ? <TaskStatusPanel personaId={workspace.persona.persona_id} taskId={primaryTask.task_id} /> : null}

      {/* Spec-035 role-aware operator panels (T036–T044, FR-001..FR-008). */}
      <div className="workspace-role-panels grid gap-4 mt-4">
        {role === "incident-commander" ? (
          <IcApprovalCard
            scenarioId={scenarioId}
            rationale="Awaiting evaluation to bind rationale, sources, and confidence."
            sources={[]}
            confidence={0}
            approverIdentity={workspace.persona.persona_id}
          />
        ) : null}
        {role === "public-information-officer" ? <PioAwsComposer /> : null}
        {role === "observer-auditor" ? (
          <ObserverAuditorTimeline rows={[]} />
        ) : null}
        {role === "risk-manager" ? <RiskMatrix scenarioId={scenarioId} /> : null}
        {role === "field-coordinator" ? <FieldCoordinatorOffline /> : null}
        {role === "planning-officer" ? (
          <PlanningIapComposer scenarioId={scenarioId} />
        ) : null}
        {role === "incident-commander" || role === "operations-officer" ? (
          <SpanOfControlWarning appRole={role} directReports={[]} />
        ) : null}
        {role === "resilience-planner" ? (
          <ResilienceHandoverPdf payloadFactory={() => ({ scenario_id: scenarioId })} />
        ) : null}
      </div>
    </section>
  );
}
