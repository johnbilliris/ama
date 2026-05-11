"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import RiskMatrix from "../../../workspaces/[personaId]/_panels/risk-matrix";
import FieldCoordinatorOffline from "../../../workspaces/[personaId]/_panels/field-coordinator-offline";

export default function SjaNtTropicalPage(): React.ReactElement {
  const scenarioId = "nt-sja-tropical";
  return (
    <SectorWorkspaceShell
      sectorCode="sja-nt-tropical"
      jurisdiction="NT"
      title="St John NT — Tropical cyclone deployment"
      fr="FR-014"
      taskId="T196"
      description="Field-coordinator offline + risk-matrix recommendation for tropical cyclone."
    >
      <RiskMatrix scenarioId={scenarioId} />
      <FieldCoordinatorOffline />
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
