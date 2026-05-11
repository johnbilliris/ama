"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import FieldCoordinatorOffline from "../../../workspaces/[personaId]/_panels/field-coordinator-offline";
import InfrastructureOverlay from "../../../../components/infrastructure-overlay";

export default function AtTasIslandIsolationPage(): React.ReactElement {
  const scenarioId = "tas-at-island-isolation";
  return (
    <SectorWorkspaceShell
      sectorCode="at-tas-island-isolation"
      jurisdiction="TAS"
      title="AT TAS — Island isolation logistics"
      fr="FR-029"
      taskId="T191"
      description="Strait/island ferry & barge resupply links with field-coordinator offline support."
    >
      <InfrastructureOverlay initialEnabled={["island_logistics"]} />
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
