/**
 * Workspaces landing page (FR-001, FR-002).
 *
 * The persona-specific workspace lives at `/workspaces/[personaId]`.
 * This index surface lets the rbac-aiims and accessibility-and-multilingual
 * suites land somewhere a11y-clean before redirecting the operator to
 * their persona workspace. Chrome mirrors the Governance Dashboard so
 * operators see one consistent visual language across the hub.
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
    <div className="mx-auto max-w-7xl">
      <header className="preparedness-header page-gutter-header">
        <p className="preparedness-kicker">Operations</p>
        <h1 className="preparedness-title">Workspaces</h1>
        <p className="preparedness-copy">
          Persona-driven entry points to the disaster response coordination hub.
          Pick a workspace below to enter the operating picture tailored to
          that AIIMS function.
        </p>
        <div
          data-testid="au-region-banner"
          role="note"
          aria-label="Data residency"
          className="mt-3 inline-flex items-center rounded border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-900"
        >
          Hosted in Australia · AU data residency
        </div>
      </header>

      <main className="p-6">
        <ul
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
          aria-label="Featured persona workspaces"
        >
          {FEATURED_PERSONAS.map((p) => (
            <li
              key={p.id}
              data-testid="workspace-card"
              className="rounded-lg border border-gray-200 bg-white p-4 transition-colors hover:border-blue-300"
            >
              <h2 className="text-base font-semibold text-gray-900">
                <Link
                  className="text-blue-700 underline"
                  href={`/workspaces/${p.id}`}
                >
                  {p.label}
                </Link>
              </h2>
              <p className="mt-1 text-sm text-gray-600">{p.description}</p>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
