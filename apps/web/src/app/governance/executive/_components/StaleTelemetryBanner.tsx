/**
 * T042 — StaleTelemetryBanner.
 *
 * Renders "stale as of <timestamp>" when the upstream telemetry sink is
 * unavailable. Honours NN-5 + FR-023.
 */
import * as React from 'react';

export interface StaleTelemetryBannerProps {
  stale: boolean;
  lastObservedUtc: string | null;
}

export function StaleTelemetryBanner(
  props: StaleTelemetryBannerProps,
): React.ReactElement | null {
  if (!props.stale) return null;
  return (
    <div role="alert" className="evidence-pack-stale-banner">
      Telemetry stale as of{' '}
      <time dateTime={props.lastObservedUtc ?? undefined}>
        {props.lastObservedUtc ?? 'unknown'}
      </time>
      . Operator action: investigate the upstream sink (App Insights / Cosmos audit).
    </div>
  );
}
