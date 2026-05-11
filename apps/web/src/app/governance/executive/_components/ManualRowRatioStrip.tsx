/**
 * T040 — ManualRowRatioStrip.
 *
 * Renders the per-artefact `manual_row_ratio` for the five evidence-pack
 * artefacts inside an `aria-live="polite"` region so screen-reader users
 * hear ratio updates as the page refreshes (NN-3 + FR-021 + FR-037).
 *
 * Composition-only — no chart libraries (RES-03, SC-009).
 */
import * as React from 'react';

export interface ManualRowRatio {
  artefact_id: string;
  manual_row_ratio: number;
}

export interface ManualRowRatioStripProps {
  ratios: ManualRowRatio[];
  /** FR-038 cap (default 0.5). Cells over this value get an `over-cap` class. */
  threshold?: number;
}

export function ManualRowRatioStrip(props: ManualRowRatioStripProps): React.ReactElement {
  const { ratios, threshold = 0.5 } = props;
  return (
    <section
      role="status"
      aria-live="polite"
      aria-label="Manual-row ratio per evidence-pack artefact"
      className="evidence-pack-ratio-strip"
    >
      <ul style={{ display: 'flex', gap: '1rem', listStyle: 'none', padding: 0, margin: 0 }}>
        {ratios.map((r) => {
          const overCap = r.manual_row_ratio > threshold;
          return (
            <li key={r.artefact_id} className={overCap ? 'over-cap' : 'within-cap'}>
              <strong>{r.artefact_id}</strong>{' '}
              <span aria-label={`manual-row ratio ${r.manual_row_ratio.toFixed(2)}`}>
                {r.manual_row_ratio.toFixed(2)} ({Math.round(r.manual_row_ratio * 100)}%)
              </span>
              {overCap ? (
                <span role="img" aria-label="over cap"> ⚠</span>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
