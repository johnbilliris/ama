"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createSimulation, ALLOWED_WARP_SPEEDS } from "@/lib/api/simulations";

const SCENARIO_TYPES = [
  { value: "Bushfire", label: "Bushfire" },
  { value: "Flood", label: "Flood" },
  { value: "Cyclone", label: "Cyclone" },
  { value: "Severe Storm", label: "Severe Storm" },
  { value: "Heatwave", label: "Heatwave" },
  { value: "Earthquake", label: "Earthquake" },
  { value: "Tsunami", label: "Tsunami" },
  { value: "Pandemic", label: "Pandemic" },
  { value: "Other", label: "Other / Multi-hazard" },
];

const JURISDICTIONS = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "NT", "ACT"];

export default function CreateSimulationPage() {
  const router = useRouter();
  const [scenarioType, setScenarioType] = useState("Bushfire");
  const [jurisdictions, setJurisdictions] = useState<string[]>(["NSW"]);
  const [maxSignals, setMaxSignals] = useState(1000);
  const [maxRecommendations, setMaxRecommendations] = useState(500);
  const [maxDurationHours, setMaxDurationHours] = useState(72);
  const [warpSpeed, setWarpSpeed] = useState<number>(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleJurisdiction = (j: string) => {
    setJurisdictions((prev) => (prev.includes(j) ? prev.filter((x) => x !== j) : [...prev, j]));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      const result = await createSimulation({
        scenario_type: scenarioType,
        jurisdictions,
        participants: [],
        warp_speed: warpSpeed,
        resource_limits: {
          max_signals: maxSignals,
          max_recommendations: maxRecommendations,
          max_duration_hours: maxDurationHours,
        },
      });
      router.push(`/simulations/${encodeURIComponent(result.tenant_id)}`);
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Create Simulation Exercise</h1>
        <Link href="/simulations" className="text-sm text-blue-600 hover:underline">
          ← Back to list
        </Link>
      </div>

      <p className="mb-6 rounded bg-amber-50 p-3 text-sm text-amber-900">
        Simulations are <strong>exercise-only</strong>. No communication events are sent to the
        real public. Chat with the Simulation Controller from the detail page once the
        exercise is created.
      </p>

      <form onSubmit={onSubmit} className="space-y-5">
        <div>
          <label htmlFor="scenario_type" className="mb-1 block text-sm font-medium">
            Scenario type
          </label>
          <select
            id="scenario_type"
            value={scenarioType}
            onChange={(e) => setScenarioType(e.target.value)}
            className="w-full rounded border px-3 py-2"
            required
          >
            {SCENARIO_TYPES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <fieldset>
          <legend className="mb-1 block text-sm font-medium">Jurisdictions</legend>
          <div className="flex flex-wrap gap-2">
            {JURISDICTIONS.map((j) => {
              const checked = jurisdictions.includes(j);
              return (
                <label
                  key={j}
                  className={`cursor-pointer rounded border px-3 py-1 text-sm ${
                    checked ? "border-blue-600 bg-blue-50 text-blue-700" : "border-gray-300"
                  }`}
                >
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={checked}
                    onChange={() => toggleJurisdiction(j)}
                  />
                  {j}
                </label>
              );
            })}
          </div>
        </fieldset>

        <div>
          <label className="mb-1 block text-sm font-medium">Exercise coordinator</label>
          <p className="rounded border bg-gray-50 px-3 py-2 text-sm text-gray-700">
            You&apos;ll be added as the exercise coordinator automatically. You can invite
            additional participants from the simulation dashboard after it&apos;s created.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <LimitInput id="max_signals" label="Max signals" value={maxSignals} onChange={setMaxSignals} />
          <LimitInput
            id="max_recs"
            label="Max recommendations"
            value={maxRecommendations}
            onChange={setMaxRecommendations}
          />
          <LimitInput
            id="max_duration"
            label="Max duration (h)"
            value={maxDurationHours}
            onChange={setMaxDurationHours}
          />
        </div>

        <fieldset>
          <legend className="mb-1 block text-sm font-medium">
            Time warp speed
            <span className="ml-2 text-xs font-normal text-gray-500">
              (scheduler delivers signals {warpSpeed}× faster than wall clock)
            </span>
          </legend>
          <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Warp speed">
            {ALLOWED_WARP_SPEEDS.map((s) => {
              const active = s === warpSpeed;
              return (
                <label
                  key={s}
                  className={`cursor-pointer rounded border px-3 py-1 text-sm ${
                    active ? "border-blue-600 bg-blue-50 text-blue-700" : "border-gray-300"
                  }`}
                >
                  <input
                    type="radio"
                    name="warp_speed"
                    className="sr-only"
                    checked={active}
                    onChange={() => setWarpSpeed(s)}
                  />
                  {s}×
                </label>
              );
            })}
          </div>
          <p className="mt-1 text-xs text-gray-500">
            Allowed: 1×, 2×, 5×, 10×, 24×, 60×. Speed can be changed during the run.
          </p>
        </fieldset>

        {error && (
          <p role="alert" className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={submitting || jurisdictions.length === 0}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {submitting ? "Creating…" : "Create simulation"}
          </button>
          <Link
            href="/simulations"
            className="rounded border border-gray-300 px-4 py-2 text-sm text-gray-700"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}

function LimitInput({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-xs font-medium">
        {label}
      </label>
      <input
        id={id}
        type="number"
        min={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value) || 0)}
        className="w-full rounded border px-2 py-1 text-sm"
      />
    </div>
  );
}
