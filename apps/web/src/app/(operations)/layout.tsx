/**
 * Layout for the regulated `(operations)` route group (spec-035 T072).
 *
 * Wraps every persona / sector workspace with the offline subsystem so the
 * service worker is registered exactly once across the route group. Field /
 * field-remote panels (e.g. `FieldCoordinatorOffline`) opt in per page.
 */

import * as React from "react";

import OfflineSubsystemBootstrap from "./_offline-bootstrap";

export default function OperationsLayout({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  return (
    <div data-route-group="operations">
      <OfflineSubsystemBootstrap />
      {children}
    </div>
  );
}
