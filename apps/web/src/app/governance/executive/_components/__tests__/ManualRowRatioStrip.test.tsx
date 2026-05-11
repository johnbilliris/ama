/**
 * T022 — ManualRowRatioStrip Vitest unit test.
 * Citations: FR-021, FR-037, NN-3, CHK080.
 */
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ManualRowRatioStrip } from '../ManualRowRatioStrip';

const ratios = [
  { artefact_id: 'risk_register', manual_row_ratio: 0.2 },
  { artefact_id: 'adoption_roadmap', manual_row_ratio: 0.3 },
  { artefact_id: 'executive_kpi_surface', manual_row_ratio: 0.1 },
  { artefact_id: 'rai_register', manual_row_ratio: 0.8 },
  { artefact_id: 'feature_value_ledger', manual_row_ratio: 0.4 },
];

describe('ManualRowRatioStrip', () => {
  it('renders 5 ratio cells', () => {
    render(<ManualRowRatioStrip ratios={ratios} />);
    expect(screen.getAllByRole('listitem')).toHaveLength(5);
  });

  it('exposes an aria-live="polite" region', () => {
    render(<ManualRowRatioStrip ratios={ratios} />);
    const live = screen.getByRole('status');
    expect(live).toHaveAttribute('aria-live', 'polite');
  });

  it('announces the ratio value in accessible text', () => {
    render(<ManualRowRatioStrip ratios={ratios} />);
    expect(screen.getByText(/risk_register/i)).toBeInTheDocument();
    expect(screen.getByText(/0\.20|20%/i)).toBeInTheDocument();
  });
});
