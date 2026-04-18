import { Suspense } from "react";

import { listJurisdictions } from "../../lib/api/jurisdictions";
import { PreparednessClient } from "../../components/preparedness/preparedness-client";

interface PreparednessPageProps {
  searchParams: Promise<{ jurisdictions?: string }>;
}

export default async function PreparednessPage({ searchParams }: PreparednessPageProps) {
  const params = await searchParams;
  const jurisdictions = await listJurisdictions().catch(() => []);

  const validIds = new Set(jurisdictions.map((j) => j.jurisdiction_id));
  const initialSelectedIds = params.jurisdictions
    ? params.jurisdictions.split(",").filter((id) => validIds.has(id))
    : [];

  return (
    <div className="incident-page">
      <Suspense fallback={<div className="preparedness-loading">Loading preparedness page…</div>}>
        <PreparednessClient jurisdictions={jurisdictions} initialSelectedIds={initialSelectedIds} />
      </Suspense>
    </div>
  );
}
