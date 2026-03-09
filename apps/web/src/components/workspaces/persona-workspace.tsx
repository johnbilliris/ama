import type { PersonaWorkspacePayload } from "../../lib/api/personas";
import { TaskStatusPanel } from "./task-status-panel";

interface PersonaWorkspaceProps {
  workspace: PersonaWorkspacePayload;
}

export function PersonaWorkspace({ workspace }: PersonaWorkspaceProps) {
  const primaryTask = workspace.tasks[0];

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
    </section>
  );
}
