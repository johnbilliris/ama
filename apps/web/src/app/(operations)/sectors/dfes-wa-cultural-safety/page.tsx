"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import PioAwsComposer from "../../../workspaces/[personaId]/_panels/pio-aws-composer";
import { CulturalSafetyPanel } from "../../../../components/cultural-safety";

export default function DfesWaCulturalSafetyPage(): React.ReactElement {
  const scenarioId = "wa-dfes-cultural-safety";
  return (
    <SectorWorkspaceShell
      sectorCode="dfes-wa-cultural-safety"
      jurisdiction="WA"
      title="DFES WA — Cultural-safety subsystem"
      fr="FR-016"
      taskId="T189"
      description="Kimberley/Pilbara elder-routing flow with PIO composer + IC approval."
    >
      <CulturalSafetyPanel
        jurisdiction="WA"
        variants={[]}
        state="pending_elder"
        awsLevel="watch_and_act"
      />
      <PioAwsComposer />
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
