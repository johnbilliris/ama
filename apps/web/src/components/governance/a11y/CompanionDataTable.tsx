"use client";

import { useState, type ReactNode } from "react";

interface CompanionDataTableProps {
  /** Caption for the data table */
  caption: string;
  /** Column headers */
  headers: string[];
  /** Row data — array of arrays matching headers. Cells may be plain
   *  strings/numbers or rich React nodes (for inline tooltips, icons, …). */
  rows: (string | number | ReactNode)[][];
  /** Optional ID for ARIA linking */
  id?: string;
}

/**
 * Visually hidden data table with toggle button for accessibility (FR-032).
 * Provides tabular representation of chart/gauge data for screen readers.
 */
export function CompanionDataTable({
  caption,
  headers,
  rows,
  id,
}: CompanionDataTableProps) {
  const [visible, setVisible] = useState(false);
  const tableId = id ?? `companion-table-${caption.replace(/\s+/g, "-").toLowerCase()}`;

  return (
    <div className="mt-2">
      <button
        onClick={() => setVisible((v) => !v)}
        className="text-xs text-blue-600 underline hover:text-blue-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        aria-expanded={visible}
        aria-controls={tableId}
      >
        {visible ? "Hide data table" : "Show data table"}
      </button>

      <div
        id={tableId}
        className={visible ? "mt-2" : "sr-only"}
        role="region"
        aria-label={caption}
      >
        <table className="min-w-full text-xs">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {headers.map((h) => (
                <th
                  key={h}
                  scope="col"
                  className="border-b px-2 py-1 text-left font-medium text-gray-700"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className="border-b px-2 py-1 text-gray-600"
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
