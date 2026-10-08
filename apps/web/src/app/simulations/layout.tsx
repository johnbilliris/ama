"use client";

/**
 * AUD-018 — route layout that owns the mandatory simulation marker for every
 * `/simulations/*` view and state (initial, loading, error, playback, report).
 *
 * AUD-017 — this layout owns exercise-local navigation after an authorised
 * operator enters the separate simulation management area.
 */
import type { PropsWithChildren } from "react";
import Link from "next/link";

import {
  SimulationExerciseMarker,
  SimulationLifecycleProvider,
} from "@/components/simulation-lifecycle";

export default function SimulationsLayout({ children }: PropsWithChildren) {
  return (
    <SimulationLifecycleProvider>
      <div className="sim-exercise-shell">
        <SimulationExerciseMarker />
        <nav className="sim-exercise-nav" aria-label="Simulation exercises">
          <Link href="/simulations">Exercises</Link>
          <span aria-hidden="true">·</span>
          <Link href="/simulations/create">New exercise</Link>
        </nav>
        <div className="sim-exercise-content">{children}</div>
      </div>
    </SimulationLifecycleProvider>
  );
}
