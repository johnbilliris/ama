"use client";

/**
 * AUD-018 — simulation identification owned at the `/simulations` layout
 * boundary so it survives loading, error, playback and report states.
 *
 * Routes publish the tenant's real lifecycle status through
 * `useReportSimulationLifecycle`; until one does, the marker shows
 * "Status pending" instead of claiming the exercise is Active.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import { SimulationBanner, type LifecycleStatus } from "@/components/simulation-banner";

/** Map an API `SimulationTenant.status` onto a banner lifecycle status. */
export function toLifecycleStatus(status?: string | null): LifecycleStatus {
  switch ((status ?? "").toLowerCase()) {
    case "active":
      return "active";
    case "paused":
      return "paused";
    case "aborted":
      return "aborted";
    case "archiving":
    case "archived":
      return "archived";
    case "completed":
      return "completed";
    default:
      return "unknown";
  }
}

interface LifecycleContextValue {
  status: LifecycleStatus;
  report: (status: LifecycleStatus) => void;
}

const SimulationLifecycleContext = createContext<LifecycleContextValue | null>(null);

export function SimulationLifecycleProvider({ children }: PropsWithChildren) {
  const [status, setStatus] = useState<LifecycleStatus>("unknown");
  const report = useCallback((next: LifecycleStatus) => setStatus(next), []);
  const value = useMemo(() => ({ status, report }), [status, report]);
  return (
    <SimulationLifecycleContext.Provider value={value}>
      {children}
    </SimulationLifecycleContext.Provider>
  );
}

export function useSimulationLifecycleStatus(): LifecycleStatus {
  return useContext(SimulationLifecycleContext)?.status ?? "unknown";
}

/** Publish the current tenant status to the layout marker. */
export function useReportSimulationLifecycle(status?: string | null): void {
  const ctx = useContext(SimulationLifecycleContext);
  const report = ctx?.report;
  useEffect(() => {
    report?.(toLifecycleStatus(status));
  }, [report, status]);
}

export function SimulationExerciseMarker() {
  const status = useSimulationLifecycleStatus();
  return <SimulationBanner status={status} />;
}
