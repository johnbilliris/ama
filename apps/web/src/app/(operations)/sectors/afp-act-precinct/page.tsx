"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import InfrastructureOverlay from "../../../../components/infrastructure-overlay";
import RiskMatrix from "../../../workspaces/[personaId]/_panels/risk-matrix";

export default function AfpActPrecinctPage(): React.ReactElement {
  const scenarioId = "act-afp-precinct";
  return (
    <SectorWorkspaceShell
      sectorCode="afp-act-precinct"
      jurisdiction="ACT"
      title="AFP ACT — Federal precinct"
      fr="FR-029"
      taskId="T193"
      description="Federal-tenancy overlay differentiating Commonwealth vs Territory governance."
    >
      <InfrastructureOverlay initialEnabled={["federal_precinct"]} />
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
