"use client";

import { useMemo, useState } from "react";

const PRINCIPLES: { value: string; label: string }[] = [
  { value: "life_safety_first", label: "I. Life Safety First" },
  { value: "multi_agent_coordination", label: "II. Multi-Agent Coordination" },
  { value: "data_trust_provenance_freshness", label: "III. Data Trust, Provenance & Freshness" },
  { value: "privacy_security_regional_policy", label: "IV. Privacy, Security & Regional Policy" },
  { value: "multilingual_accessible_actionable", label: "V. Multilingual, Accessible & Actionable" },
  { value: "cloud_platform", label: "VI. Cloud Platform" },
];

const STATUSES: { value: string; label: string }[] = [
  { value: "compliant", label: "Compliant" },
  { value: "partially_compliant", label: "Partially compliant" },
  { value: "non_compliant", label: "Non-compliant" },
  { value: "not_applicable", label: "Not applicable" },
];

const TRIGGERS: { value: string; label: string }[] = [
  { value: "initial_review", label: "Initial review" },
  { value: "source_change", label: "Source change" },
  { value: "constitution_amendment", label: "Constitution amendment" },
];

interface AssessmentFormProps {
  dataSourceId: string;
  onCreated: () => void;
}

function splitLines(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

export function AssessmentForm({ dataSourceId, onCreated }: AssessmentFormProps) {
  const [principle, setPrinciple] = useState(PRINCIPLES[0].value);
  const [status, setStatus] = useState(STATUSES[0].value);
  const [explanation, setExplanation] = useState("");
  const [conditionsText, setConditionsText] = useState("");
  const [gapsText, setGapsText] = useState("");
  const [assessorId, setAssessorId] = useState("");
  const [triggeredBy, setTriggeredBy] = useState(TRIGGERS[0].value);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const requiresConditions = status === "partially_compliant";
  const requiresGaps = status === "partially_compliant" || status === "non_compliant";

  const conditions = useMemo(() => splitLines(conditionsText), [conditionsText]);
  const gaps = useMemo(() => splitLines(gapsText), [gapsText]);

  const validationError = (() => {
    if (!explanation.trim()) return "Explanation is required.";
    if (!assessorId.trim()) return "Assessor ID is required.";
    if (requiresConditions && conditions.length === 0) {
      return "At least one condition is required for partially compliant assessments.";
    }
    if (requiresGaps && gaps.length === 0) {
      return "At least one gap is required for partially compliant or non-compliant assessments.";
    }
    return null;
  })();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (validationError) {
      setError(validationError);
      return;
    }
    setSubmitting(true);
    try {
      const response = await fetch(
        `/api/data-sources/${encodeURIComponent(dataSourceId)}/compliance`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            principle,
            compliance_status: status,
            explanation: explanation.trim(),
            conditions,
            gaps,
            assessor_id: assessorId.trim(),
            triggered_by: triggeredBy,
          }),
        },
      );
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || `Request failed: ${response.status}`);
      }
      setSuccess(`Recorded ${status.replace(/_/g, " ")} assessment for ${principle.replace(/_/g, " ")}.`);
      setExplanation("");
      setConditionsText("");
      setGapsText("");
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record assessment.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-gray-200 bg-white p-4">
      <h2 className="text-lg font-semibold">Record Assessment</h2>
      <p className="text-xs text-gray-500">
        Records a new constitutional assessment. The previous current assessment for the same principle is
        automatically superseded.
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Constitutional principle</span>
          <select
            value={principle}
            onChange={(e) => setPrinciple(e.target.value)}
            className="mt-1 block w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
          >
            {PRINCIPLES.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="font-medium text-gray-700">Compliance status</span>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="mt-1 block w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
          >
            {STATUSES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="font-medium text-gray-700">Assessor ID</span>
          <input
            type="text"
            value={assessorId}
            onChange={(e) => setAssessorId(e.target.value)}
            placeholder="e.g. alice@gov.au"
            className="mt-1 block w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
          />
        </label>

        <label className="block text-sm">
          <span className="font-medium text-gray-700">Triggered by</span>
          <select
            value={triggeredBy}
            onChange={(e) => setTriggeredBy(e.target.value)}
            className="mt-1 block w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
          >
            {TRIGGERS.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </label>
      </div>

      <label className="block text-sm">
        <span className="font-medium text-gray-700">Explanation</span>
        <textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          rows={3}
          placeholder="Describe the basis for this assessment."
          className="mt-1 block w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
        />
      </label>

      <label className="block text-sm">
        <span className="font-medium text-gray-700">
          Conditions{requiresConditions ? " (required)" : " (optional)"}
        </span>
        <textarea
          value={conditionsText}
          onChange={(e) => setConditionsText(e.target.value)}
          rows={3}
          placeholder="One condition per line."
          className="mt-1 block w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
        />
      </label>

      <label className="block text-sm">
        <span className="font-medium text-gray-700">
          Gaps{requiresGaps ? " (required)" : " (optional)"}
        </span>
        <textarea
          value={gapsText}
          onChange={(e) => setGapsText(e.target.value)}
          rows={3}
          placeholder="One gap per line."
          className="mt-1 block w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
        />
      </label>

      {error && (
        <div role="alert" className="rounded border border-red-200 bg-red-50 p-2 text-sm text-red-800">
          {error}
        </div>
      )}
      {success && (
        <div role="status" className="rounded border border-green-200 bg-green-50 p-2 text-sm text-green-800">
          {success}
        </div>
      )}

      <div className="flex items-center justify-end gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? "Saving…" : "Record assessment"}
        </button>
      </div>
    </form>
  );
}
