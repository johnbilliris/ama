import { AppShell } from "@ama/ui/components/layout/app-shell";

export default function HomePage() {
  return (
    <AppShell>
      <div className="incident-page">
        <h1>Autonomous Disaster Response Coordination Hub</h1>
        <p>Select an incident, workspace, or preparedness analysis to begin.</p>
      </div>
    </AppShell>
  );
}
