interface DegradedModeBannerProps {
  contradictedCount: number;
}

export function DegradedModeBanner({ contradictedCount }: DegradedModeBannerProps) {
  if (contradictedCount === 0) {
    return null;
  }

  return (
    <section className="degraded-banner">
      <strong>Reduced-function advisory</strong>
      <p className="degraded-copy">
        {contradictedCount} contradicted or degraded signal(s) detected. Recommendations remain under manual review until corroborated.
      </p>
    </section>
  );
}
