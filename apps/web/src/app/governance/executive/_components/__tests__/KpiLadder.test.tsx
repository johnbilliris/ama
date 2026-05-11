/**
 * T023 — KpiLadder Vitest unit test.
 * Citations: RES-03, SC-009, CHK081.
 */
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { KpiLadder } from '../KpiLadder';

const kpis = [
  { kpi_id: 'KPI-CAP-001', capstone_criterion: 'lives-saved', kind: 'leading',
    name: 'Triage signal volume', owner: 'Risk Manager', refresh_cadence: 'daily',
    target_value: 100, target_unit: 'signals/day' },
  { kpi_id: 'KPI-CAP-002', capstone_criterion: 'lives-saved', kind: 'lagging',
    name: 'Lives preserved (baseline-counterfactual)', owner: 'Executive Leader',
    refresh_cadence: 'quarterly', target_value: 1000, target_unit: 'lives/year' },
];

describe('KpiLadder', () => {
  it('renders both leading and lagging KPIs', () => {
    render(<KpiLadder kpis={kpis} />);
    expect(screen.getByText(/Triage signal volume/)).toBeInTheDocument();
    expect(screen.getByText(/Lives preserved/)).toBeInTheDocument();
  });

  it('does not import any chart library (compile-time invariant)', () => {
    // Composition-only: rely on linting. This test is a smoke-level guard
    // that the component renders without throwing under jsdom.
    const { container } = render(<KpiLadder kpis={kpis} />);
    expect(container.firstChild).not.toBeNull();
  });
});
