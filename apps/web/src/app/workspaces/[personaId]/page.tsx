"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { PersonaWorkspace } from "../../../components/workspaces/persona-workspace";
import {
  getPersonaWorkspace,
  PersonaWorkspaceError,
  type PersonaWorkspacePayload,
} from "../../../lib/api/personas";
import { ConnectivityBanner } from "../../../components/offline/connectivity-banner";
import { useI18n } from "../../../lib/i18n/runtime";
import { useParams, useSearchParams } from "next/navigation";

type LoadState =
  | { status: "loading" }
  | { status: "loaded"; workspace: PersonaWorkspacePayload }
  | { status: "error"; httpStatus: number; message: string };

export default function WorkspacePage() {
  const { t } = useI18n();
  const params = useParams<{ personaId: string }>();
  const searchParams = useSearchParams();
  const personaId = params.personaId;
  const incidentId = searchParams.get("incidentId") ?? "incident-001";
  const [state, setState] = useState<LoadState>({ status: "loading" });

  async function refreshWorkspace() {
    const workspace = await getPersonaWorkspace(personaId, incidentId);
    setState({ status: "loaded", workspace });
  }

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    getPersonaWorkspace(personaId, incidentId)
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
  }, [personaId, incidentId]);

  if (state.status === "loading") {
    return (
      <div className="incident-page" role="status" aria-live="polite">
        <p>{t("workspace.loading")}</p>
      </div>
    );
  }

  if (state.status === "error") {
    const isNotFound = state.httpStatus === 404;
    return (
      <div className="incident-page" role="alert">
        <h1 className="text-xl font-semibold text-slate-900">
          {isNotFound ? t("workspace.notFound") : t("workspace.failed")}
        </h1>
        <p className="mt-2 text-sm text-slate-700">
          {isNotFound
            ? t("workspace.notFoundBody", { personaId })
            : state.message}
        </p>
        <p className="mt-4">
          <Link className="text-blue-700 underline" href="/workspaces">
            {t("common.backToWorkspaces")}
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="incident-page">
      <ConnectivityBanner />
      <nav aria-label="Workspace breadcrumb" className="mb-3 text-sm">
        <Link className="text-blue-700 underline" href="/workspaces">
          ← {t("common.backToWorkspaces")}
        </Link>
      </nav>
      <PersonaWorkspace
        workspace={state.workspace}
        incidentId={incidentId}
        tenantId="live"
        mode="live"
        onWorkspaceChanged={refreshWorkspace}
      />
    </div>
  );
}
