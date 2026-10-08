import type { PersonaWorkspacePayload } from "../../lib/api/personas";
import { useState } from "react";
import { TaskStatusPanel } from "./task-status-panel";
import FieldCoordinatorOffline from "../../app/workspaces/[personaId]/_panels/field-coordinator-offline";
import IcApprovalCard from "../../app/workspaces/[personaId]/_panels/ic-approval-card";
import ObserverAuditorTimeline from "../../app/workspaces/[personaId]/_panels/observer-auditor-timeline";
import PioAwsComposer from "../../app/workspaces/[personaId]/_panels/pio-aws-composer";
import PlanningIapComposer from "../../app/workspaces/[personaId]/_panels/planning-iap-composer";
import ResilienceHandoverPdf from "../../app/workspaces/[personaId]/_panels/resilience-handover-pdf";
import RiskMatrix from "../../app/workspaces/[personaId]/_panels/risk-matrix";
import SpanOfControlWarning from "../../app/workspaces/[personaId]/_panels/span-of-control-warning";
import { useI18n } from "../../lib/i18n/runtime";
import { WorkspaceShell } from "./workspace-shell";

interface PersonaWorkspaceProps {
  workspace: PersonaWorkspacePayload;
  incidentId: string;
  tenantId?: string;
  mode?: "live" | "rehearsal";
  onWorkspaceChanged: () => Promise<void>;
}

export function PersonaWorkspace({
  workspace,
  incidentId,
  tenantId = "live",
  mode = "live",
  onWorkspaceChanged,
}: PersonaWorkspaceProps) {
  const { t } = useI18n();
  const [approvalStatus, setApprovalStatus] = useState<string>("");
  const primaryTask = workspace.tasks[0];
  const role = workspace.persona.role.replace(/-/g, "_");
  const scenarioId = primaryTask?.task_id ?? "0";

  return (
    <WorkspaceShell
      kicker={workspace.persona.role}
      title={workspace.persona.display_name}
      subtitle={workspace.persona.organisation_id}
    >
      <div className="workspace-columns">
        <article className="workspace-panel">
          <h2 className="workspace-panel-title">{t("workspace.assignedTasks")}</h2>
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
          <h2 className="workspace-panel-title">{t("workspace.dependencies")}</h2>
          <ul className="workspace-list">
            {workspace.dependencies.length === 0 ? (
              <li className="workspace-list-item">{t("workspace.noDependencies")}</li>
            ) : (
              workspace.dependencies.map((task) => (
                <li key={task.taskId} className="workspace-list-item">
                  <strong>{task.title}</strong>
                  <div className="workspace-meta">{task.status} · owner {task.ownerOrganisationId}</div>
                </li>
              ))
            )}
          </ul>
        </article>
      </div>

      {workspace.tasks.length > 0 ? (
        <TaskStatusPanel
          personaId={workspace.persona.persona_id}
          incidentId={incidentId}
          tenantId={tenantId}
          mode={mode}
          tasks={workspace.tasks.map((task) => ({
            task_id: task.task_id,
            title: task.title,
            status: task.status as "queued" | "in_progress" | "blocked" | "completed",
            version: task.version,
          }))}
          onUpdated={onWorkspaceChanged}
        />
      ) : null}

      {/* Spec-035 role-aware operator panels (T036–T044, FR-001..FR-008). */}
      <div className="workspace-role-panels grid gap-4 mt-4">
        {role === "incident_commander" ? (
          <IcApprovalCard
            scenarioId={scenarioId}
            rationale="Awaiting evaluation to bind rationale, sources, and confidence."
            sources={[]}
            confidence={0}
            approverIdentity={workspace.persona.persona_id}
          />
        ) : null}
        {role === "public_information_officer" ? (
          <>
            <PioAwsComposer
              onApprovalRequest={() => {
                setApprovalStatus("Approval request submitted for commander review.");
              }}
            />
            {approvalStatus ? <p role="status">{approvalStatus}</p> : null}
          </>
        ) : null}
        {role === "observer_auditor" ? (
          <ObserverAuditorTimeline rows={[]} />
        ) : null}
        {role === "risk_manager" ? <RiskMatrix scenarioId={scenarioId} /> : null}
        {role === "field_coordinator" ? <FieldCoordinatorOffline /> : null}
        {role === "planning_officer" ? (
          <PlanningIapComposer scenarioId={scenarioId} />
        ) : null}
        {role === "incident_commander" || role === "operations_officer" ? (
          <SpanOfControlWarning appRole={role} directReports={[]} />
        ) : null}
        {role === "resilience_planner" ? (
          <ResilienceHandoverPdf payloadFactory={() => ({ scenario_id: scenarioId })} />
        ) : null}
      </div>
    </WorkspaceShell>
  );
}
