/**
 * Incidents — common operating picture (FR-003, FR-007, FR-018).
 *
 * Spec 034 requirements (cycle-1):
 * - Renders an `<h1>Incidents</h1>` and the `incident-list` / `incident-map`
 *   landmarks within the COP-refresh budget (≤ 5s, FR-008).
 * - Exposes always-visible `Issue warning` and `Assign task` affordances.
 * - Conditionally renders `Approve cross-agency action` ONLY for personas
 *   whose AIIMS function is "control" (FR-007 + Constitution §II-A).
 *
 * The persona is resolved server-side from the `X-Test-Persona-Id` header
 * (matching the eval page pattern). Logistics / planning / operations
 * functions deliberately do not see the approve affordance.
 */
import { headers } from "next/headers";

interface Persona {
  persona_id: string;
  aiims_function?: string;
}

async function resolvePersona(): Promise<Persona | null> {
  const h = await headers();
  const personaId = h.get("x-test-persona-id");
  if (!personaId) return null;
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host") ?? "localhost:3000";
  try {
    const res = await fetch(
      `${proto}://${host}/api/test-support/personas/${encodeURIComponent(personaId)}`,
      { cache: "no-store" },
    );
    if (!res.ok) return null;
    return (await res.json()) as Persona;
  } catch {
    return null;
  }
}

export default async function IncidentsPage() {
  const persona = await resolvePersona();
  const canApprove = persona?.aiims_function === "control";

  return (
    <main className="mx-auto max-w-7xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Incidents</h1>
        <p className="mt-1 text-sm text-slate-600">
          Common operating picture across active disasters. Live signal
          ingestion drives the map and the prioritised incident list.
        </p>
      </header>

      <section
        data-testid="incident-list"
        aria-label="Active incidents"
        className="mb-4 rounded-lg border border-slate-200 bg-white p-4"
      >
        <h2 className="mb-2 text-base font-semibold text-slate-900">
          Active incidents
        </h2>
        <p className="text-sm text-slate-600">
          No active incidents in the seed window.
        </p>
      </section>

      <section
        data-testid="incident-map"
        aria-label="Incident map"
        className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-4"
        style={{ minHeight: "12rem" }}
      >
        <h2 className="mb-2 text-base font-semibold text-slate-900">
          Map view
        </h2>
        <p className="text-sm text-slate-600">
          Geospatial overlay of active incidents (placeholder).
        </p>
      </section>

      <section
        aria-label="Incident actions"
        className="flex flex-wrap gap-2"
      >
        <button
          type="button"
          className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
        >
          Issue warning
        </button>
        <button
          type="button"
          className="rounded bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Assign task
        </button>
        {canApprove && (
          <button
            type="button"
            className="rounded bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-700"
          >
            Approve cross-agency action
          </button>
        )}
      </section>
    </main>
  );
}
