"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  addParticipants,
  createSimulation,
  seedReplay,
  seedSimulation,
  ALLOWED_WARP_SPEEDS,
  SCENARIO_TEMPLATES,
  type ParticipantAssignment,
} from "@/lib/api/simulations";

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

type SeedSource = "none" | "template" | "replay";

interface ParticipantRow extends ParticipantAssignment {
  key: string;
}

function emptyParticipantRow(): ParticipantRow {
  return {
    key: `p-${Math.random().toString(36).slice(2)}`,
    oid: "",
    persona: "",
    organisation_id: "",
    jurisdiction_id: "",
    role: "participant",
  };
}

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
  const [seedSource, setSeedSource] = useState<SeedSource>("none");
  const [templateId, setTemplateId] = useState<string>(SCENARIO_TEMPLATES[0].template_id);
  const [replayIncidentId, setReplayIncidentId] = useState("");
  const [replayStart, setReplayStart] = useState("");
  const [replayEnd, setReplayEnd] = useState("");
  const [participants, setParticipants] = useState<ParticipantRow[]>([]);

  const toggleJurisdiction = (j: string) => {
    setJurisdictions((prev) => (prev.includes(j) ? prev.filter((x) => x !== j) : [...prev, j]));
  };

  const updateParticipant = (key: string, patch: Partial<ParticipantAssignment>) => {
    setParticipants((prev) => prev.map((p) => (p.key === key ? { ...p, ...patch } : p)));
  };

  const assignedParticipants = (): ParticipantAssignment[] =>
    participants
      .filter((p) => p.oid.trim().length > 0)
      .map(({ oid, persona, organisation_id, jurisdiction_id, role }) => ({
        oid: oid.trim(),
        ...(persona?.trim() ? { persona: persona.trim() } : {}),
        ...(organisation_id?.trim() ? { organisation_id: organisation_id.trim() } : {}),
        ...(jurisdiction_id?.trim() ? { jurisdiction_id: jurisdiction_id.trim() } : {}),
        role: role?.trim() || "participant",
      }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    let tenantId: string;
    try {
      const result = await createSimulation({
        scenario_type: scenarioType,
        jurisdictions,
        participants: [],
        ...(seedSource === "template" ? { scenario_template_id: templateId } : {}),
        warp_speed: warpSpeed,
        resource_limits: {
          max_signals: maxSignals,
          max_recommendations: maxRecommendations,
          max_duration_hours: maxDurationHours,
        },
      });
      tenantId = result.tenant_id;
    } catch (err) {
      setError(`Create failed: ${(err as Error).message}`);
      setSubmitting(false);
      return;
    }

    // Post-create steps are reported individually: a partial failure must not
    // look like a clean create, and must not discard the created tenant.
    const followUpFailures: string[] = [];
    const assignments = assignedParticipants();
    if (assignments.length > 0) {
      try {
        await addParticipants(tenantId, assignments);
      } catch (err) {
        followUpFailures.push(`participant assignment: ${(err as Error).message}`);
      }
    }
    if (seedSource === "template") {
      try {
        await seedSimulation(tenantId, templateId);
      } catch (err) {
        followUpFailures.push(`template seed: ${(err as Error).message}`);
      }
    } else if (seedSource === "replay") {
      try {
        await seedReplay(tenantId, replayIncidentId.trim(), replayStart, replayEnd);
      } catch (err) {
        followUpFailures.push(`historical replay: ${(err as Error).message}`);
      }
    }

    if (followUpFailures.length > 0) {
      setError(
        `Exercise ${tenantId} was created, but these steps failed — ${followUpFailures.join("; ")}. ` +
          "Retry them from the exercise dashboard.",
      );
      setSubmitting(false);
      return;
    }
    router.push(`/simulations/${encodeURIComponent(tenantId)}`);
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

        <fieldset data-testid="seed-source">
          <legend className="mb-1 block text-sm font-medium">Initial scenario data</legend>
          <div className="space-y-2">
            {([
              ["none", "Empty exercise — seed later from the controller chat"],
              ["template", "Seed from a curated scenario template"],
              ["replay", "Replay a historical incident window"],
            ] as [SeedSource, string][]).map(([value, label]) => (
              <label key={value} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="seed_source"
                  value={value}
                  checked={seedSource === value}
                  onChange={() => setSeedSource(value)}
                />
                {label}
              </label>
            ))}
          </div>

          {seedSource === "template" && (
            <div className="mt-3">
              <label htmlFor="template_id" className="mb-1 block text-xs font-medium">
                Scenario template
              </label>
              <select
                id="template_id"
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
                className="w-full rounded border px-3 py-2 text-sm"
              >
                {SCENARIO_TEMPLATES.map((t) => (
                  <option key={t.template_id} value={t.template_id}>
                    {t.name} ({t.scenario_type})
                  </option>
                ))}
              </select>
            </div>
          )}

          {seedSource === "replay" && (
            <div className="mt-3 grid grid-cols-3 gap-3">
              <div className="col-span-3">
                <label htmlFor="replay_incident" className="mb-1 block text-xs font-medium">
                  Source incident ID
                </label>
                <input
                  id="replay_incident"
                  value={replayIncidentId}
                  onChange={(e) => setReplayIncidentId(e.target.value)}
                  className="w-full rounded border px-3 py-2 text-sm"
                  placeholder="incident-…"
                  required
                />
              </div>
              <div className="col-span-3 grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="replay_start" className="mb-1 block text-xs font-medium">
                    Window start
                  </label>
                  <input
                    id="replay_start"
                    type="datetime-local"
                    value={replayStart}
                    onChange={(e) => setReplayStart(e.target.value)}
                    className="w-full rounded border px-3 py-2 text-sm"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="replay_end" className="mb-1 block text-xs font-medium">
                    Window end
                  </label>
                  <input
                    id="replay_end"
                    type="datetime-local"
                    value={replayEnd}
                    onChange={(e) => setReplayEnd(e.target.value)}
                    className="w-full rounded border px-3 py-2 text-sm"
                    required
                  />
                </div>
              </div>
            </div>
          )}
        </fieldset>

        <fieldset data-testid="participant-assignments">
          <legend className="mb-1 block text-sm font-medium">Participant assignments</legend>
          <p className="mb-2 text-xs text-gray-500">
            You are added as the exercise coordinator automatically. Each additional
            participant needs an Entra object ID; persona, organisation and jurisdiction
            are persisted with the assignment.
          </p>
          <div className="space-y-2">
            {participants.map((p) => (
              <div key={p.key} className="grid grid-cols-12 gap-2">
                <input
                  aria-label="Participant object ID"
                  value={p.oid}
                  onChange={(e) => updateParticipant(p.key, { oid: e.target.value })}
                  placeholder="Entra object ID"
                  className="col-span-4 rounded border px-2 py-1 text-sm"
                />
                <input
                  aria-label="Participant persona"
                  value={p.persona ?? ""}
                  onChange={(e) => updateParticipant(p.key, { persona: e.target.value })}
                  placeholder="persona"
                  className="col-span-2 rounded border px-2 py-1 text-sm"
                />
                <input
                  aria-label="Participant organisation"
                  value={p.organisation_id ?? ""}
                  onChange={(e) => updateParticipant(p.key, { organisation_id: e.target.value })}
                  placeholder="organisation"
                  className="col-span-2 rounded border px-2 py-1 text-sm"
                />
                <input
                  aria-label="Participant jurisdiction"
                  value={p.jurisdiction_id ?? ""}
                  onChange={(e) => updateParticipant(p.key, { jurisdiction_id: e.target.value })}
                  placeholder="jurisdiction"
                  className="col-span-2 rounded border px-2 py-1 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setParticipants((prev) => prev.filter((x) => x.key !== p.key))}
                  aria-label={`Remove participant ${p.oid || "row"}`}
                  className="col-span-2 rounded border border-gray-300 px-2 py-1 text-sm"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setParticipants((prev) => [...prev, emptyParticipantRow()])}
            className="mt-2 rounded border border-gray-300 px-3 py-1 text-sm"
          >
            Add participant
          </button>
        </fieldset>

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
