interface SourceHealthPanelProps {
  authoritativeCount: number;
  communityCount: number;
  contradictedCount: number;
}

export function SourceHealthPanel({
  authoritativeCount,
  communityCount,
  contradictedCount,
}: SourceHealthPanelProps) {
  const cards = [
    { label: "Authoritative", value: authoritativeCount, tone: "#0d6b79" },
    { label: "Community", value: communityCount, tone: "#0b8a5f" },
    { label: "Contradicted", value: contradictedCount, tone: "#c55a11" },
  ];

  return (
    <section>
      <h2 className="source-health-title">Signal health</h2>
      <div className="source-health-grid">
        {cards.map((card) => (
          <article key={card.label} className="source-health-card">
            <div className="source-health-label">{card.label}</div>
            <div className={`source-health-value ${card.label.toLowerCase()}`}>{card.value}</div>
          </article>
        ))}
      </div>
    </section>
  );
}
