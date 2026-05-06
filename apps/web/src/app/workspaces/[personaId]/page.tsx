"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { PersonaWorkspace } from "../../../components/workspaces/persona-workspace";
import {
  getPersonaWorkspace,
  PersonaWorkspaceError,
  type PersonaWorkspacePayload,
} from "../../../lib/api/personas";
import { useParams } from "next/navigation";

type LoadState =
  | { status: "loading" }
  | { status: "loaded"; workspace: PersonaWorkspacePayload }
  | { status: "error"; httpStatus: number; message: string };

export default function WorkspacePage() {
  const params = useParams<{ personaId: string }>();
  const personaId = params.personaId;
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    getPersonaWorkspace(personaId)
      .then((workspace) => {
        if (!cancelled) setState({ status: "loaded", workspace });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof PersonaWorkspaceError) {
          setState({
            status: "error",
            httpStatus: error.status,
            message: error.message,
          });
        } else {
          setState({
            status: "error",
            httpStatus: 0,
            message: error instanceof Error ? error.message : "Failed to load workspace",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [personaId]);

  if (state.status === "loading") {
    return (
      <div className="incident-page" role="status" aria-live="polite">
        <p>Loading workspace…</p>
      </div>
    );
  }

  if (state.status === "error") {
    const isNotFound = state.httpStatus === 404;
    return (
      <div className="incident-page" role="alert">
        <h1 className="text-xl font-semibold text-slate-900">
          {isNotFound ? "Workspace not found" : "Workspace failed to load"}
        </h1>
        <p className="mt-2 text-sm text-slate-700">
          {isNotFound
            ? `No persona with id "${personaId}" is registered. Pick a persona from the workspaces directory.`
            : state.message}
        </p>
        <p className="mt-4">
          <Link className="text-blue-700 underline" href="/workspaces">
            Back to workspaces
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="incident-page">
      <nav aria-label="Workspace breadcrumb" className="mb-3 text-sm">
        <Link className="text-blue-700 underline" href="/workspaces">
          ← Back to workspaces
        </Link>
      </nav>
      <PersonaWorkspace workspace={state.workspace} />
    </div>
  );
}
