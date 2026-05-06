"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import PlanningIapComposer from "../../../workspaces/[personaId]/_panels/planning-iap-composer";
import InfrastructureOverlay from "../../../../components/infrastructure-overlay";

export default function SesActDeclarationPage(): React.ReactElement {
  const scenarioId = "act-ses-declaration";
  return (
    <SectorWorkspaceShell
      sectorCode="ses-act-declaration"
      jurisdiction="ACT"
      title="ACT SES — Declaration / collision overlay"
      fr="FR-029"
      taskId="T194"
      description="Federal vs territory declaration collision with precinct overlay."
    >
      <InfrastructureOverlay initialEnabled={["federal_precinct"]} />
      <PlanningIapComposer scenarioId={scenarioId} />
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
