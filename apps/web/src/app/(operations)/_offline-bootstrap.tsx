/**
 * Offline subsystem bootstrap for every regulated `(operations)` route.
 *
 * Registers the offline service worker on first mount so that any field /
 * field-remote persona route gains queue-on-disconnect semantics.
 * Spec-035 T072 / FR-006.
 */

"use client";

import * as React from "react";

import { registerOfflineServiceWorker } from "@/lib/offline/service-worker";

export default function OfflineSubsystemBootstrap(): null {
  React.useEffect(() => {
    void registerOfflineServiceWorker();
  }, []);
  return null;
}
