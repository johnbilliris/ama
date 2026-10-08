"use client";
import { getApiBaseUrl } from "@/lib/api/base-url";

import { useMemo, useState } from "react";

import { updateTaskStatus, type TaskStatus } from "../../lib/api/tasks";
import { createOfflineQueueStore } from "../../lib/offline/queue-store";
import { useI18n } from "../../lib/i18n/runtime";

interface TaskStatusPanelProps {
  personaId: string;
  incidentId: string;
  tenantId?: string;
  mode?: "live" | "rehearsal";
  tasks: Array<{
    task_id: string;
    title: string;
    status: TaskStatus;
    version?: number;
  }>;
  onUpdated: () => Promise<void>;
}

export function TaskStatusPanel({
  personaId,
  incidentId,
  tenantId = "live",
  mode = "live",
  tasks,
  onUpdated,
}: TaskStatusPanelProps) {
  const { t } = useI18n();
  const [selectedTaskId, setSelectedTaskId] = useState<string>(tasks[0]?.task_id ?? "");
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState(false);

  const selectedTask = useMemo(
    () => tasks.find((task) => task.task_id === selectedTaskId) ?? tasks[0],
    [tasks, selectedTaskId],
  );

  async function transition(status: TaskStatus) {
    if (!selectedTask) return;
    setBusy(true);
    setError("");
    try {
      await updateTaskStatus({
        taskId: selectedTask.task_id,
        personaId,
        status,
        blockerReason: status === "blocked" ? "Awaiting inter-agency dependency completion" : undefined,
        ifMatch: selectedTask.version,
      });
      await onUpdated();
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Task update failed";
      const shouldQueue =
        typeof navigator !== "undefined" && (!navigator.onLine || /HTTP 5\d\d/.test(message) || /Network/i.test(message));

      if (shouldQueue && selectedTask) {
        const store = await createOfflineQueueStore();
        try {
          const queued = await store.enqueue({
            persona_id: personaId,
            actor_id: personaId,
            tenant_id: tenantId,
            incident_id: incidentId,
            mode,
            client_correlation_id: crypto.randomUUID(),
            tier: "routine",
            method: "PATCH",
            route: `${getApiBaseUrl()}/tasks/${selectedTask.task_id}`,
            payload: {
              personaId,
              status,
              blockerReason: status === "blocked" ? "Awaiting inter-agency dependency completion" : undefined,
              ifMatch: selectedTask.version,
            },
            captured_ts: new Date().toISOString(),
            expires_ts: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            attempts: 0,
          });
          if (queued.status === "rejected" && queued.reason === "crypto_unavailable") {
            setError(t("workspace.cryptoBlocked"));
          } else {
            setError(t("workspace.offlineQueued"));
          }
        } finally {
          store.close();
        }
      } else {
        setError(message);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="workspace-status-panel">
      <label className="workspace-status-copy" htmlFor="workspace-task-select">{t("workspace.selectedTask")}</label>
      <select
        id="workspace-task-select"
        className="workspace-status-button"
        value={selectedTask?.task_id ?? ""}
        onChange={(event) => setSelectedTaskId(event.target.value)}
        disabled={busy || tasks.length === 0}
      >
        {tasks.map((task) => (
          <option key={task.task_id} value={task.task_id}>
            {task.title} ({task.status})
          </option>
        ))}
      </select>

      <div className="workspace-columns">
        <button type="button" className="workspace-status-button" onClick={() => transition("in_progress")} disabled={busy || !selectedTask}>
          {t("workspace.start")}
        </button>
        <button type="button" className="workspace-status-button" onClick={() => transition("blocked")} disabled={busy || !selectedTask}>
          {t("workspace.block")}
        </button>
        <button type="button" className="workspace-status-button" onClick={() => transition("completed")} disabled={busy || !selectedTask}>
          {t("workspace.complete")}
        </button>
      </div>

      {error ? <p className="workspace-status-copy" role="alert">{error}</p> : null}
    </section>
  );
}
