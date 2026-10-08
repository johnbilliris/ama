interface DegradedModeBannerProps {
  degradedSources?: Array<{
    sourceId: string;
    status: string;
    reason: string;
    since: string;
  }>;
}

export function DegradedModeBanner({ degradedSources = [] }: DegradedModeBannerProps) {
  if (degradedSources.length === 0) {
    return null;
  }

  return (
    <section className="degraded-banner" data-testid="degraded-mode-banner">
      <strong>Reduced-function advisory</strong>
      <p className="degraded-copy">
        {degradedSources.length} degraded source(s) detected. Recommendations remain under manual review until corroborated.
      </p>
      <ul>
        {degradedSources.map((source) => (
          <li key={`${source.sourceId}-${source.since}`}>
            {source.sourceId}: {source.status} ({source.reason})
          </li>
        ))}
      </ul>
    </section>
  );
}
