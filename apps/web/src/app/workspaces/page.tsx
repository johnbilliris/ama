/**
 * Workspaces landing page (FR-001, FR-002).
 *
 * The persona-specific workspace lives at `/workspaces/[personaId]`.
 * This index surface lets the rbac-aiims and accessibility-and-multilingual
 * suites land somewhere a11y-clean before redirecting the operator to
 * their persona workspace.
 */
import Link from "next/link";

const FEATURED_PERSONAS: Array<{ id: string; label: string; description: string }> = [
  {
    id: "incident-commander",
    label: "Incident Commander",
    description: "Full operating picture with cross-agency approval authority.",
  },
  {
    id: "operations-officer",
    label: "Operations Officer",
    description: "Tasking, resourcing, and tactical co-ordination.",
  },
  {
    id: "planning-officer",
    label: "Planning Officer",
    description: "Forward planning, evacuation timing, and recovery handover.",
  },
  {
    id: "logistics-officer",
    label: "Logistics Officer",
    description: "DACC, mutual aid, and surge logistics.",
  },
  {
    id: "public-information-officer",
    label: "Public Information Officer",
    description: "Multilingual warnings and community communications.",
  },
  {
    id: "executive-leader",
    label: "Executive Leader",
    description: "Constitutional governance, dashboards, and recovery oversight.",
  },
];

export default function WorkspacesIndexPage() {
  return (
    <main className="mx-auto max-w-7xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Workspaces</h1>
        <p className="mt-1 text-sm text-slate-600">
          Persona-driven entry points to the disaster response coordination hub.
          Pick a workspace below to enter the operating picture tailored to
          that AIIMS function.
        </p>
      </header>

      <ul
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
        aria-label="Featured persona workspaces"
      >
        {FEATURED_PERSONAS.map((p) => (
          <li
            key={p.id}
            data-testid="workspace-card"
            className="rounded-lg border border-slate-200 bg-white p-4 hover:border-blue-300"
          >
            <h2 className="text-base font-semibold text-slate-900">
              <Link
                className="text-blue-700 underline"
                href={`/workspaces/${p.id}`}
              >
                {p.label}
              </Link>
            </h2>
            <p className="mt-1 text-sm text-slate-600">{p.description}</p>
          </li>
        ))}
      </ul>
    </main>
  );
}
