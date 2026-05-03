/**
 * Governance — Data Sources (FR-014, FR-018(a)).
 *
 * Spec 034 requirements (cycle-1):
 * - Renders an `<h1>Data Sources</h1>` and the `data-source-table` landmark.
 * - Acts as a placeholder admin surface; the FR-018(a) data-multiplicity
 *   invariant is proved through the FR-028 evaluator audit chain rather
 *   than via this page.
 */
export default function DataSourcesPage() {
  return (
    <main className="mx-auto max-w-7xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Data Sources</h1>
        <p className="mt-1 text-sm text-slate-600">
          Registered upstream feeds powering the common operating picture and
          governance audit trail.
        </p>
      </header>

      <section
        data-testid="data-source-table"
        aria-label="Registered data sources"
        className="rounded-lg border border-slate-200 bg-white"
      >
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <caption className="sr-only">Registered data sources</caption>
          <thead className="bg-slate-50 text-slate-700">
            <tr>
              <th scope="col" className="px-4 py-2 text-left font-semibold">Source</th>
              <th scope="col" className="px-4 py-2 text-left font-semibold">Owner</th>
              <th scope="col" className="px-4 py-2 text-left font-semibold">Cadence</th>
              <th scope="col" className="px-4 py-2 text-left font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            <tr>
              <td colSpan={4} className="px-4 py-6 text-center text-slate-500">
                Source registry rendered from
                <code className="mx-1 font-mono text-xs">
                  packages/domain/src/domain/seed/data_sources_australia.json
                </code>
                — admin tooling forthcoming.
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>
  );
}
