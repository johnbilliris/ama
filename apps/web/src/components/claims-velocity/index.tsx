/**
 * Claims-velocity dashboard (T052, FR-024 / data-model § 12).
 *
 * Renders the ICA claims-velocity snapshot with sortable LGA breakdown.
 */

"use client";

import * as React from "react";

export interface LgaBreakdownRow {
  lga_code: string;
  lga_name: string;
  claims_lodged: number;
  claims_closed: number;
  dollars_lodged: number;
  dollars_paid: number;
}

export interface ClaimsVelocitySnapshot {
  as_at: string;
  claims_lodged: number;
  claims_closed: number;
  dollars_lodged: number;
  dollars_paid: number;
  lga_breakdown: LgaBreakdownRow[];
}

export interface ClaimsVelocityDashboardProps {
  snapshot: ClaimsVelocitySnapshot;
}

type SortKey = keyof Omit<LgaBreakdownRow, "lga_code" | "lga_name">;

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function ClaimsVelocityDashboard(
  props: ClaimsVelocityDashboardProps,
): React.ReactElement {
  const { snapshot } = props;
  const [sortKey, setSortKey] = React.useState<SortKey>("claims_lodged");
  const [sortDir, setSortDir] = React.useState<"asc" | "desc">("desc");

  const sorted = React.useMemo(() => {
    const copy = [...snapshot.lga_breakdown];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      return sortDir === "asc" ? av - bv : bv - av;
    });
    return copy;
  }, [snapshot.lga_breakdown, sortKey, sortDir]);

  const closeRate =
    snapshot.claims_lodged === 0
      ? 0
      : snapshot.claims_closed / snapshot.claims_lodged;
  const payRate =
    snapshot.dollars_lodged === 0
      ? 0
      : snapshot.dollars_paid / snapshot.dollars_lodged;

  const setSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="claims-velocity-dashboard"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Claims velocity (ICA)</h2>
        <span className="text-xs text-slate-500">
          as at {snapshot.as_at}
        </span>
      </header>
      <dl className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
        <div>
          <dt className="text-xs text-slate-500">Claims lodged</dt>
          <dd className="font-mono">{snapshot.claims_lodged.toLocaleString()}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">
            Claims closed ({(closeRate * 100).toFixed(0)}%)
          </dt>
          <dd className="font-mono">{snapshot.claims_closed.toLocaleString()}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">$ lodged</dt>
          <dd className="font-mono">{formatCurrency(snapshot.dollars_lodged)}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">
            $ paid ({(payRate * 100).toFixed(0)}%)
          </dt>
          <dd className="font-mono">{formatCurrency(snapshot.dollars_paid)}</dd>
        </div>
      </dl>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-xs">
          <caption className="sr-only">LGA breakdown of claims velocity.</caption>
          <thead>
            <tr className="text-left">
              <th>LGA</th>
              {(
                [
                  ["claims_lodged", "Lodged"],
                  ["claims_closed", "Closed"],
                  ["dollars_lodged", "$ lodged"],
                  ["dollars_paid", "$ paid"],
                ] as const
              ).map(([key, label]) => (
                <th key={key} className="pl-3">
                  <button
                    type="button"
                    onClick={() => setSort(key)}
                    aria-sort={
                      sortKey === key
                        ? sortDir === "asc"
                          ? "ascending"
                          : "descending"
                        : "none"
                    }
                    className="underline"
                  >
                    {label}
                    {sortKey === key ? (sortDir === "asc" ? " ▲" : " ▼") : ""}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => (
              <tr key={row.lga_code} className="border-t border-slate-100">
                <td className="py-1 font-mono">{row.lga_name}</td>
                <td className="pl-3">{row.claims_lodged.toLocaleString()}</td>
                <td className="pl-3">{row.claims_closed.toLocaleString()}</td>
                <td className="pl-3">{formatCurrency(row.dollars_lodged)}</td>
                <td className="pl-3">{formatCurrency(row.dollars_paid)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default ClaimsVelocityDashboard;
