"use client";

import { startTransition, useDeferredValue, useState } from "react";

import { updateTaskStatus } from "../../lib/api/tasks";

interface TaskStatusPanelProps {
  personaId: string;
  taskId: string;
}

export function TaskStatusPanel({ personaId, taskId }: TaskStatusPanelProps) {
  const [lastUpdate, setLastUpdate] = useState("queued");
  const deferredLastUpdate = useDeferredValue(lastUpdate);

  function handleStartTask() {
    startTransition(async () => {
      const response = await updateTaskStatus(taskId, personaId, "in_progress");
      setLastUpdate(response.status);
    });
  }

  return (
    <section className="workspace-status-panel">
      <button type="button" className="workspace-status-button" onClick={handleStartTask}>
        Start selected task
      </button>
      <p className="workspace-status-copy">Last update: {deferredLastUpdate}</p>
    </section>
  );
}
