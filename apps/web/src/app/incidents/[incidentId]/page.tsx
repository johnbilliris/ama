"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@ama/ui/components/layout/app-shell";
import { PublicAlertComposer } from "../../../components/alerts/public-alert-composer";
import { SharedOperatingPicture } from "../../../components/dashboard/shared-operating-picture";
import { getIncidentDashboard, type DashboardPayload } from "../../../lib/api/dashboard";
import { listSignals, type SignalRecord } from "../../../lib/api/signals";
import { useParams } from "next/navigation";

export default function IncidentPage() {
  const params = useParams<{ incidentId: string }>();
  const incidentId = params.incidentId;
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [signals, setSignals] = useState<SignalRecord[]>([]);

  useEffect(() => {
    Promise.all([
      getIncidentDashboard(incidentId),
      listSignals(incidentId),
    ]).then(([d, s]) => {
      setDashboard(d);
      setSignals(s);
    });
  }, [incidentId]);

  if (!dashboard) {
    return (
      <AppShell>
        <div className="incident-page"><p>Loading incident…</p></div>
      </AppShell>
    );
  }

  const firstRecommendation = dashboard.activeRecommendations[0];
  const alertId = firstRecommendation ? `alert-${firstRecommendation.recommendation_id}` : "alert-pending";

  return (
    <AppShell>
      <div className="incident-page">
        <SharedOperatingPicture dashboard={dashboard} signals={signals} />
        {firstRecommendation ? (
          <PublicAlertComposer recommendationId={firstRecommendation.recommendation_id} alertId={alertId} />
        ) : null}
      </div>
    </AppShell>
  );
}
