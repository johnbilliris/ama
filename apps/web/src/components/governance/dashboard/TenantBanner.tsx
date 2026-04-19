"use client";

interface TenantBannerProps {
  /** Tenant display name (e.g., "SIMULATION — scenario-1") */
  tenantDisplayName: string;
  /** Whether this is a simulation tenant */
  isSimulation: boolean;
}

/**
 * Persistent non-dismissible simulation mode indicator banner (FR-026A).
 * Uses --ama-sim-banner colour token.
 */
export function TenantBanner({
  tenantDisplayName,
  isSimulation,
}: TenantBannerProps) {
  if (!isSimulation) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="border-b-2 border-purple-400 bg-purple-100 px-6 py-2 text-center text-sm font-bold text-purple-900"
      style={{
        borderColor: "var(--ama-sim-banner, #9333ea)",
        backgroundColor: "var(--ama-sim-banner-bg, #f3e8ff)",
      }}
    >
      🔬 {tenantDisplayName}
    </div>
  );
}
