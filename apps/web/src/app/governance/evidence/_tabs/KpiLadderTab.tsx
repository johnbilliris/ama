import PublicInformationChannels from "./PublicInformationChannels";

export default function KpiLadderTab() {
  return (
    <div data-testid="evidence-kpi-ladder-tab">
      <p>KPI Ladder — populated by Phase 3.</p>
      <PublicInformationChannels jurisdiction="AU" />
    </div>
  );
}

