"use client";

import { useState } from "react";
import { WorkspaceShell } from "../../../../components/workspaces/workspace-shell";
import AuditTab from "./AuditTab";
import BenchmarkTab from "./BenchmarkTab";
import ImpactTab from "./ImpactTab";
import KpiLadderTab from "./KpiLadderTab";
import MeasurementTab from "./MeasurementTab";
import PublicInformationChannels from "./PublicInformationChannels";
import ReplayTab from "./ReplayTab";

const TABS = [
  { id: "kpi-ladder", label: "KPI Ladder" },
  { id: "measurement", label: "Measurement Method" },
  { id: "replay", label: "Replay Scorecard" },
  { id: "impact", label: "Impact Chains" },
  { id: "benchmarks", label: "Benchmarks" },
  { id: "audit", label: "Audit Trace" },
  { id: "public-information", label: "Public Information" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function EvidenceWorkspace() {
  const [activeTab, setActiveTab] = useState<TabId>("kpi-ladder");
  const [selectedValueId, setSelectedValueId] = useState("");

  return (
    <WorkspaceShell
      ariaLabel="Evidence Harness"
      kicker="Governance · Evidence"
      title="Measurable Success-Criteria Evidence Harness"
      subtitle="Advisory only · AU sovereignty · Append-only audit"
      footer={
        <p className="workspace-banner" role="note">
          Advisory only — no autonomous action.
        </p>
      }
    >
      <nav aria-label="Evidence views" className="workspace-tabs">
        <div role="tablist" aria-label="Evidence views">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              id={`${tab.id}-tab`}
              type="button"
              role="tab"
              aria-controls={`${tab.id}-panel`}
              aria-selected={activeTab === tab.id}
              tabIndex={activeTab === tab.id ? 0 : -1}
              onClick={() => setActiveTab(tab.id)}
              className="rounded px-3 py-2 text-sm font-medium"
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>
      <div className="workspace-tabpanels">
        {TABS.map((tab) => (
          <section
            key={tab.id}
            id={`${tab.id}-panel`}
            role="tabpanel"
            aria-labelledby={`${tab.id}-tab`}
            hidden={activeTab !== tab.id}
            className="workspace-panel"
          >
            <h2 className="workspace-panel-title">{tab.label}</h2>
            {tab.id === "kpi-ladder" ? <KpiLadderTab /> : null}
            {tab.id === "measurement" ? <MeasurementTab /> : null}
            {tab.id === "replay" ? (
              <ReplayTab onScorecardSelected={setSelectedValueId} />
            ) : null}
            {tab.id === "impact" ? <ImpactTab /> : null}
            {tab.id === "benchmarks" ? <BenchmarkTab /> : null}
            {tab.id === "audit" ? (
              <AuditTab initialValueId={selectedValueId} />
            ) : null}
            {tab.id === "public-information" ? (
              <PublicInformationChannels />
            ) : null}
          </section>
        ))}
      </div>
    </WorkspaceShell>
  );
}
