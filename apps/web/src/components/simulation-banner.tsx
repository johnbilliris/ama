"use client";

export function SimulationBanner() {
  return (
    <div
      className="simulation-banner"
      role="alert"
      aria-live="assertive"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        backgroundColor: "#dc2626",
        color: "#ffffff",
        textAlign: "center",
        padding: "8px 16px",
        fontWeight: 700,
        fontSize: "14px",
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        pointerEvents: "none",
        userSelect: "none",
      }}
    >
      ⚠ SIMULATION — This is not live data ⚠
    </div>
  );
}
