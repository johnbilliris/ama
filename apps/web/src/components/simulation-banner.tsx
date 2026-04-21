"use client";

export function SimulationBanner() {
  return (
    <div className="sim-banner-wrap" role="alert" aria-live="assertive">
      <div className="sim-banner-card">
        <p className="sim-banner-kicker">⚠ Exercise mode</p>
        <h2 className="sim-banner-title">Simulation — this is not live data</h2>
        <p className="sim-banner-copy">
          All communications, decisions and telemetry on this page are scoped to
          the exercise tenant. No real-world dispatch or public notifications
          will be issued.
        </p>
      </div>
    </div>
  );
}
