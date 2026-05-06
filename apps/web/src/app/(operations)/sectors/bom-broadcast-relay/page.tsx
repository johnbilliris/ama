"use client";

import * as React from "react";
import SectorWorkspaceShell from "../_shell";
import IcApprovalCard from "../../../workspaces/[personaId]/_panels/ic-approval-card";
import PioAwsComposer from "../../../workspaces/[personaId]/_panels/pio-aws-composer";
import { CulturalSafetyPanel } from "../../../../components/cultural-safety";

export default function BomBroadcastRelayPage(): React.ReactElement {
  const scenarioId = "commonwealth-bom-broadcast";
  const [acknowledged, setAcknowledged] = React.useState(false);

  return (
    <SectorWorkspaceShell
      sectorCode="bom-broadcast-relay"
      jurisdiction="Commonwealth"
      title="BoM Broadcast Relay"
      fr="FR-014"
      taskId="T197"
      description="BoM observation streams → multilingual broadcast script with broadcaster acknowledgement."
    >
      <PioAwsComposer />
      <CulturalSafetyPanel
        jurisdiction="AU"
        variants={[]}
        state="pending_elder"
        awsLevel="advice"
      />
      <section
        className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
        data-testid="broadcast-acknowledgement"
      >
        <h2 className="text-lg font-semibold">Broadcaster acknowledgement</h2>
        <p className="text-sm text-slate-600">
          Relay completion requires explicit broadcaster acknowledgement.
        </p>
        <button
          type="button"
          onClick={() => setAcknowledged(true)}
          disabled={acknowledged}
          className="mt-2 rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          data-testid="broadcast-ack-btn"
        >
          {acknowledged ? "Acknowledged" : "Confirm relay"}
        </button>
      </section>
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
