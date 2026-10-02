/**
 * Vitest for the persona workspace page error handling.
 *
 * Regression for the deployed-app bug where a 404 response left the page on
 * "Loading workspace…" forever. The page now distinguishes loading / error /
 * loaded states and renders a clear "Workspace not found" message with a
 * back-link instead of stalling.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import React from "react";
import { I18nProvider } from "../src/lib/i18n/runtime";

vi.mock("next/navigation", () => ({
  useParams: () => ({ personaId: "incident_commander_au_east" }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children }: { href: string; children: React.ReactNode }) =>
    React.createElement("a", { href }, children),
}));

const getPersonaWorkspaceMock = vi.fn();

vi.mock("../src/lib/api/personas", async () => {
  const actual = await vi.importActual<typeof import("../src/lib/api/personas")>(
    "../src/lib/api/personas",
  );
  return {
    ...actual,
    getPersonaWorkspace: (...args: unknown[]) => getPersonaWorkspaceMock(...args),
  };
});

describe("workspaces/[personaId] page", () => {
  beforeEach(() => {
    getPersonaWorkspaceMock.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders 'Workspace not found' UI on 404 instead of staying on Loading", async () => {
    const { PersonaWorkspaceError } = await import("../src/lib/api/personas");
    getPersonaWorkspaceMock.mockRejectedValueOnce(
      new PersonaWorkspaceError("Persona not found", 404),
    );

    const { default: WorkspacePage } = await import(
      "../src/app/workspaces/[personaId]/page"
    );

    render(
      <I18nProvider>
        <WorkspacePage />
      </I18nProvider>,
    );

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("Workspace not found"),
    );
    expect(screen.queryByText("Loading workspace…")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Back to workspaces/i })).toHaveAttribute(
      "href",
      "/workspaces",
    );
  });

  it("renders a generic failure message for non-404 errors", async () => {
    const { PersonaWorkspaceError } = await import("../src/lib/api/personas");
    getPersonaWorkspaceMock.mockRejectedValueOnce(
      new PersonaWorkspaceError("Service unavailable", 503),
    );

    const { default: WorkspacePage } = await import(
      "../src/app/workspaces/[personaId]/page"
    );

    render(
      <I18nProvider>
        <WorkspacePage />
      </I18nProvider>,
    );

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("Workspace failed to load"),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Service unavailable");
  });

  it("renders a 'Back to workspaces' link when the workspace loads successfully", async () => {
    getPersonaWorkspaceMock.mockResolvedValueOnce({
      persona: {
        persona_id: "incident-commander",
        display_name: "Fiona Reilly",
        organisation_id: "org-nema",
        jurisdiction_id: "commonwealth",
        role: "incident-commander",
      },
      tasks: [],
      dependencies: [],
    });

    const { default: WorkspacePage } = await import(
      "../src/app/workspaces/[personaId]/page"
    );

    render(
      <I18nProvider>
        <WorkspacePage />
      </I18nProvider>,
    );

    const backLink = await screen.findByRole("link", { name: /Back to workspaces/i });
    expect(backLink).toHaveAttribute("href", "/workspaces");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
