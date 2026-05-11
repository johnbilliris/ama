"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import PioAwsComposer from "../../../workspaces/[personaId]/_panels/pio-aws-composer";
import { CulturalSafetyPanel } from "../../../../components/cultural-safety";

export default function TasPolMultilingualPage(): React.ReactElement {
  const scenarioId = "tas-pol-multilingual";
  return (
    <SectorWorkspaceShell
      sectorCode="taspol-multilingual"
      jurisdiction="TAS"
      title="Tasmania Police — multilingual public warnings"
      fr="FR-016"
      taskId="T192"
      description="palawa kani elder-routing + Simplified Chinese fallback chain."
    >
      <CulturalSafetyPanel
        jurisdiction="TAS"
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
