"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import ResilienceHandoverPdf from "../../../workspaces/[personaId]/_panels/resilience-handover-pdf";
import {
  ClaimsVelocityDashboard,
  type ClaimsVelocitySnapshot,
} from "../../../../components/claims-velocity";

const PLACEHOLDER_SNAPSHOT: ClaimsVelocitySnapshot = {
  as_at: new Date().toISOString(),
  claims_lodged: 0,
  claims_closed: 0,
  dollars_lodged: 0,
  dollars_paid: 0,
  lga_breakdown: [],
};

export default function UtilityInsuranceRecoveryPage(): React.ReactElement {
  const scenarioId = "cross-sector-utility-insurance-recovery";
  return (
    <SectorWorkspaceShell
      sectorCode="utility-insurance-recovery"
      jurisdiction="Cross-sector"
      title="Utility / Insurance recovery (SC-005)"
      fr="FR-024"
      taskId="T199"
      description="ICA claims-velocity dashboard wired to the recovery handover PDF for outcome-5 binding."
    >
      <ClaimsVelocityDashboard snapshot={PLACEHOLDER_SNAPSHOT} />
      <ResilienceHandoverPdf payloadFactory={() => ({ scenario_id: scenarioId })} />
    </SectorWorkspaceShell>
  );
}
