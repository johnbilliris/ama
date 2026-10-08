import { Suspense } from "react";

import { PreparednessClient } from "../../components/preparedness/preparedness-client";
import { ConnectivityBanner } from "../../components/offline/connectivity-banner";

interface PreparednessPageProps {
  searchParams: Promise<{ jurisdictions?: string }>;
}

export default async function PreparednessPage({ searchParams }: PreparednessPageProps) {
  const params = await searchParams;
  const initialJurisdictionParam = params.jurisdictions ?? "";

  return (
    <div className="incident-page">
      <ConnectivityBanner />
      <Suspense fallback={<div className="preparedness-loading">Loading preparedness page…</div>}>
        <PreparednessClient initialJurisdictionParam={initialJurisdictionParam} />
      </Suspense>
    </div>
  );
}
