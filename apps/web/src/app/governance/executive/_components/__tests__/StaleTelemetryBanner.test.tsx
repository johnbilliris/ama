/**
 * T024 — StaleTelemetryBanner Vitest unit test.
 * Citations: FR-023, NN-5, CHK082.
 */
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StaleTelemetryBanner } from '../StaleTelemetryBanner';

describe('StaleTelemetryBanner', () => {
  it('renders nothing when telemetry is fresh', () => {
    const { container } = render(
      <StaleTelemetryBanner stale={false} lastObservedUtc={null} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders "stale as of <ts>" when telemetry is stale', () => {
    render(
      <StaleTelemetryBanner stale={true} lastObservedUtc="2026-05-10T12:00:00Z" />
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/stale as of/i)).toBeInTheDocument();
    expect(screen.getByText(/2026-05-10T12:00:00Z/)).toBeInTheDocument();
  });
});
