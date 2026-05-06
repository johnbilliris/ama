"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import PioAwsComposer from "../../../workspaces/[personaId]/_panels/pio-aws-composer";
import { CulturalSafetyPanel } from "../../../../components/cultural-safety";

export default function NtesMultilingualPage(): React.ReactElement {
  const scenarioId = "nt-ntes-multilingual";
  return (
    <SectorWorkspaceShell
      sectorCode="ntes-multilingual"
      jurisdiction="NT"
      title="NTES — Multilingual cultural safety"
      fr="FR-016"
      taskId="T195"
      description="Yolŋu Matha / Pitjantjatjara / Warlpiri elder-routing + Simplified Chinese fallback."
    >
      <CulturalSafetyPanel
        jurisdiction="NT"
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
