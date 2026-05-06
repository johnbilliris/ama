"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import RiskMatrix from "../../../workspaces/[personaId]/_panels/risk-matrix";
import PioAwsComposer from "../../../workspaces/[personaId]/_panels/pio-aws-composer";

export default function NemaDaccJatwcPage(): React.ReactElement {
  const scenarioId = "commonwealth-nema-dacc-jatwc";
  return (
    <SectorWorkspaceShell
      sectorCode="nema-dacc-jatwc"
      jurisdiction="Commonwealth"
      title="NEMA DACC / JATWC tsunami coordination"
      fr="FR-014"
      taskId="T198"
      description="Joint Australian Tsunami Warning Centre coordination with risk-matrix + AWS broadcast."
    >
      <RiskMatrix scenarioId={scenarioId} />
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
