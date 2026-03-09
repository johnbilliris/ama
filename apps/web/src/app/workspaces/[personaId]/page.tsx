"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@ama/ui/components/layout/app-shell";
import { PersonaWorkspace } from "../../../components/workspaces/persona-workspace";
import { getPersonaWorkspace, type PersonaWorkspacePayload } from "../../../lib/api/personas";
import { useParams } from "next/navigation";

export default function WorkspacePage() {
  const params = useParams<{ personaId: string }>();
  const personaId = params.personaId;
  const [workspace, setWorkspace] = useState<PersonaWorkspacePayload | null>(null);

  useEffect(() => {
    getPersonaWorkspace(personaId).then(setWorkspace);
  }, [personaId]);

  if (!workspace) {
    return (
      <AppShell>
        <div className="incident-page"><p>Loading workspace…</p></div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="incident-page">
        <PersonaWorkspace workspace={workspace} />
      </div>
    </AppShell>
  );
}
