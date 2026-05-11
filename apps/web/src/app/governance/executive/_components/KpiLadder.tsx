/**
 * T041 — KpiLadder.
 *
 * Composition-only renderer for the Executive KPI Surface ladder. Groups
 * KPIs by capstone criterion and renders leading + lagging columns side by
 * side. NO chart libraries (RES-03, SC-009 — verified by grep test in T041).
 *
 * Citations: FR-019, FR-021, SC-009.
 */
import * as React from 'react';

export interface KpiSummary {
  kpi_id: string;
  capstone_criterion: string;
  kind: 'leading' | 'lagging';
  name: string;
  owner: string;
  refresh_cadence: string;
  target_value: number;
  target_unit: string;
  current_value?: number;
  last_observed_utc?: string;
}

export interface KpiLadderProps {
  kpis: KpiSummary[];
}

export function KpiLadder(props: KpiLadderProps): React.ReactElement {
  const grouped = props.kpis.reduce<Record<string, KpiSummary[]>>((acc, k) => {
    (acc[k.capstone_criterion] ??= []).push(k);
    return acc;
  }, {});

  return (
    <div className="kpi-ladder">
      {Object.entries(grouped).map(([criterion, rows]) => (
        <section key={criterion} aria-labelledby={`crit-${criterion}`}>
          <h3 id={`crit-${criterion}`}>{criterion}</h3>
          <table>
            <thead>
              <tr>
                <th scope="col">KPI</th>
                <th scope="col">Kind</th>
                <th scope="col">Owner</th>
                <th scope="col">Cadence</th>
                <th scope="col">Target</th>
                <th scope="col">Current</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((k) => (
                <tr key={k.kpi_id}>
                  <th scope="row">{k.name}</th>
                  <td>{k.kind}</td>
                  <td>{k.owner}</td>
                  <td>{k.refresh_cadence}</td>
                  <td>
                    {k.target_value} {k.target_unit}
                  </td>
                  <td>
                    {k.current_value !== undefined ? (
                      <>
                        {k.current_value} {k.target_unit}
                      </>
                    ) : (
                      <em>n/a</em>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}
