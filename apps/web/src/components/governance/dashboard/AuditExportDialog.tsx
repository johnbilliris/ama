"use client";

import { useState } from "react";

interface AuditExportDialogProps {
  /** Number of records to export */
  recordCount: number;
  /** Applied filter summary */
  filterSummary: string;
  /** Callback to start export */
  onExport: (format: "pdf" | "csv" | "json") => void;
  /** Close the dialog */
  onClose: () => void;
  /** Export job status */
  status?: "idle" | "exporting" | "complete" | "failed";
  /** Download URL when complete */
  downloadUrl?: string | null;
  /** Error message on failure */
  errorMessage?: string | null;
  /** Progress percentage */
  progress?: number;
}

/**
 * Audit export dialog with format selection, progress bar, and download link (US3).
 */
export function AuditExportDialog({
  recordCount,
  filterSummary,
  onExport,
  onClose,
  status = "idle",
  downloadUrl,
  errorMessage,
  progress = 0,
}: AuditExportDialogProps) {
  const [format, setFormat] = useState<"pdf" | "csv" | "json">("csv");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Export audit records">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Export Audit Records</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" aria-label="Close export dialog">✕</button>
        </div>

        {/* Scope summary */}
        <div className="mb-4 rounded bg-gray-50 p-3 text-sm text-gray-600">
          <p><strong>{recordCount}</strong> record{recordCount !== 1 ? "s" : ""} selected</p>
          {filterSummary && <p className="mt-1 text-xs text-gray-500">Filters: {filterSummary}</p>}
        </div>

        {status === "idle" && (
          <>
            {/* Format selection */}
            <fieldset className="mb-4">
              <legend className="mb-2 text-sm font-medium text-gray-700">Export Format</legend>
              <div className="flex gap-4">
                {(["pdf", "csv", "json"] as const).map((f) => (
                  <label key={f} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="format"
                      value={f}
                      checked={format === f}
                      onChange={() => setFormat(f)}
                      className="text-blue-600"
                    />
                    <span className="text-sm uppercase">{f}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <button
              onClick={() => onExport(format)}
              className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Start Export
            </button>
          </>
        )}

        {status === "exporting" && (
          <div>
            <p className="mb-2 text-sm text-gray-600">Generating export...</p>
            <div className="h-2 w-full rounded-full bg-gray-200">
              <div
                className="h-2 rounded-full bg-blue-600 transition-all"
                style={{ width: `${progress}%` }}
                role="progressbar"
                aria-valuenow={progress}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">{progress}% complete</p>
          </div>
        )}

        {status === "complete" && downloadUrl && (
          <div className="text-center">
            <p className="mb-3 text-sm text-green-700">✓ Export complete!</p>
            <a
              href={downloadUrl}
              download
              className="inline-block rounded-md bg-green-600 px-6 py-2 text-sm font-medium text-white hover:bg-green-700"
            >
              Download
            </a>
          </div>
        )}

        {status === "failed" && (
          <div className="text-center">
            <p className="mb-2 text-sm text-red-700">✗ Export failed</p>
            {errorMessage && <p className="text-xs text-red-600">{errorMessage}</p>}
            <button
              onClick={() => onExport(format)}
              className="mt-3 rounded-md bg-red-100 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-200"
            >
              Retry
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
