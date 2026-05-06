"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import FieldCoordinatorOffline from "../../../workspaces/[personaId]/_panels/field-coordinator-offline";
import PlanningIapComposer from "../../../workspaces/[personaId]/_panels/planning-iap-composer";

export default function SesSaMultiLgaPage(): React.ReactElement {
  const scenarioId = "sa-ses-multi-lga";
  return (
    <SectorWorkspaceShell
      sectorCode="ses-sa-multi-lga"
      jurisdiction="SA"
      title="SES SA — Multi-LGA evacuation"
      fr="FR-015"
      taskId="T188"
      description="Coordinates evacuation across multiple LGAs with field-coordinator offline support."
    >
      <IcApprovalCard
        scenarioId={scenarioId}
        rationale="Awaiting evaluation"
        sources={[]}
        confidence={0}
        approverIdentity="incident-commander"
      />
      <FieldCoordinatorOffline />
      <PlanningIapComposer scenarioId={scenarioId} />
    </SectorWorkspaceShell>
  );
}
