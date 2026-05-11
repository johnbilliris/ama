"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import InfrastructureOverlay from "../../../../components/infrastructure-overlay";
import RiskMatrix from "../../../workspaces/[personaId]/_panels/risk-matrix";

export default function DfesWaIronOrePage(): React.ReactElement {
  const scenarioId = "wa-dfes-iron-ore";
  return (
    <SectorWorkspaceShell
      sectorCode="dfes-wa-iron-ore"
      jurisdiction="WA"
      title="DFES WA — Iron-ore haul-road risk"
      fr="FR-029"
      taskId="T190"
      description="Iron-ore haul road infrastructure overlay with $-throughput sensitivity."
    >
      <InfrastructureOverlay initialEnabled={["iron_ore_haul_road", "port_critical"]} />
      <RiskMatrix scenarioId={scenarioId} />
      <IcApprovalCard
        scenarioId={scenarioId}
        rationale="Awaiting evaluation"
        sources={[]}
        confidence={0}
        approverIdentity="incident-commander"
      />
    </SectorWorkspaceShell>
  );
}
