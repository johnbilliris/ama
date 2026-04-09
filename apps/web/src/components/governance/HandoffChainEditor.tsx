"use client";

import { useState } from "react";

interface HandoffStepData {
  step_order: number;
  source_agent: string;
  target_agent: string;
  confidence_threshold: number | null;
  category_filter: string[];
}

const AGENTS = ["monitoring", "risk_assessment", "evacuation", "resource_allocation", "communication"];

const CATEGORIES = [
  "weather", "hydrology", "fire", "geohazard",
  "infrastructure", "community_report", "social_report", "resource_status",
];

interface HandoffChainEditorProps {
  dataSourceId: string;
  apiBase?: string;
  onSaved?: () => void;
}

export function HandoffChainEditor({ dataSourceId, apiBase = "/api/v1", onSaved }: HandoffChainEditorProps) {
  const [steps, setSteps] = useState<HandoffStepData[]>([
    { step_order: 1, source_agent: "", target_agent: "", confidence_threshold: null, category_filter: [] },
  ]);
  const [saving, setSaving] = useState(false);

  const addStep = () => {
    const last = steps[steps.length - 1];
    setSteps([...steps, {
      step_order: steps.length + 1,
      source_agent: last?.target_agent ?? "",
      target_agent: "",
      confidence_threshold: null,
      category_filter: [],
    }]);
  };

  const updateStep = (index: number, field: keyof HandoffStepData, value: unknown) => {
    const updated = [...steps];
    updated[index] = { ...updated[index], [field]: value };
    setSteps(updated);
  };

  const save = async () => {
    setSaving(true);
    await fetch(`${apiBase}/data-sources/${dataSourceId}/governance/handoff-chain`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ steps, created_by: "ui-user" }),
    });
    setSaving(false);
    onSaved?.();
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Handoff Chain</h3>
      {steps.map((step, i) => (
        <div key={i} className="flex items-center gap-2 rounded border p-2">
          <span className="text-xs font-medium text-gray-500">#{step.step_order}</span>
          <select value={step.source_agent} onChange={(e) => updateStep(i, "source_agent", e.target.value)} className="rounded border px-1 py-0.5 text-sm" aria-label={`Step ${step.step_order} source agent`}>
            <option value="">Source...</option>
            {AGENTS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <span className="text-gray-400">&rarr;</span>
          <select value={step.target_agent} onChange={(e) => updateStep(i, "target_agent", e.target.value)} className="rounded border px-1 py-0.5 text-sm" aria-label={`Step ${step.step_order} target agent`}>
            <option value="">Target...</option>
            {AGENTS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <input
            type="number" step="0.1" min="0" max="1"
            placeholder="Threshold"
            value={step.confidence_threshold ?? ""}
            onChange={(e) => updateStep(i, "confidence_threshold", e.target.value ? parseFloat(e.target.value) : null)}
            className="w-20 rounded border px-1 py-0.5 text-sm"
            aria-label={`Step ${step.step_order} confidence threshold`}
          />
        </div>
      ))}
      <div className="flex gap-2">
        <button onClick={addStep} className="rounded bg-gray-200 px-3 py-1 text-sm">+ Add Step</button>
        <button onClick={save} disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white disabled:opacity-50">
          {saving ? "Saving..." : "Save Chain"}
        </button>
      </div>
    </div>
  );
}
