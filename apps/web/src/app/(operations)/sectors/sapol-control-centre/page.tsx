"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import RiskMatrix from "../../../workspaces/[personaId]/_panels/risk-matrix";
import SpanOfControlWarning from "../../../workspaces/[personaId]/_panels/span-of-control-warning";

export default function SaPolControlCentrePage(): React.ReactElement {
  const scenarioId = "sa-pol-state-control";
  return (
    <SectorWorkspaceShell
      sectorCode="sapol-control-centre"
      jurisdiction="SA"
      title="SAPOL State Control Centre"
      fr="FR-014"
      taskId="T187"
      description="Multi-LGA coordination dashboard with role-separation enforcement on routes."
    >
      <IcApprovalCard
        scenarioId={scenarioId}
        rationale="Awaiting evaluation"
        sources={[]}
        confidence={0}
        approverIdentity="incident-commander"
      />
      <RiskMatrix scenarioId={scenarioId} />
      <SpanOfControlWarning appRole="incident-commander" directReports={[]} />
    </SectorWorkspaceShell>
  );
}
