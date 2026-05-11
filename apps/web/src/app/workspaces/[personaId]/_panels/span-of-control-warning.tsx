/**
 * Span-of-control warning panel (T043, FR-008).
 *
 * Surfaces the > 7-direct-reports warning before save with delegation options
 * for the IC role; suppressed for Planning Officer (read-only).
 */

"use client";

import * as React from "react";

const THRESHOLD = 7;

export interface SpanOfControlWarningProps {
  appRole: string;
  directReports: { id: string; name: string }[];
  onDelegate?: (delegateeId: string) => void;
}

export function SpanOfControlWarning(
  props: SpanOfControlWarningProps,
): React.ReactElement | null {
  const { appRole, directReports, onDelegate } = props;
  if (appRole === "planning-officer") return null;
  if (directReports.length <= THRESHOLD) return null;

  const isIC = appRole === "incident-commander";

  return (
    <section
      role="alert"
      className="rounded-md border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900"
      data-testid="span-of-control-warning"
    >
      <p className="font-semibold">
        Span-of-control exceeded ({directReports.length} of {THRESHOLD} maximum).
      </p>
      <p className="text-xs">
        FR-008 requires delegation before persistence. Save is blocked until the
        span is reduced.
      </p>
      {isIC ? (
        <ul className="mt-2 ml-5 list-disc">
          {directReports.map((dr) => (
            <li key={dr.id} className="flex items-center justify-between">
              <span>{dr.name}</span>
              <button
                type="button"
                onClick={() => onDelegate?.(dr.id)}
                className="ml-2 underline"
              >
                Delegate
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-xs">
          Delegation must be performed by the Incident Commander.
        </p>
      )}
    </section>
  );
}

export default SpanOfControlWarning;
