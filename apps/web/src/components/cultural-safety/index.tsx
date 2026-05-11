/**
 * Cultural-safety panel (T050, FR-016).
 *
 * Surfaces the language-pack registry, elder-approval routing state, and
 * the fallback-chain renderer.
 */

"use client";

import * as React from "react";

import {
  listAvailableLanguages,
  resolveLanguageVariant,
  type LanguagePackId,
  type LanguageVariant,
} from "../../lib/i18n/language-packs";

export type CulturalSafetyState =
  | "pending_elder"
  | "approved"
  | "declined"
  | "timeout_lifesafety_override"
  | "timeout_blocked";

export interface CulturalSafetyPanelProps {
  jurisdiction: string;
  variants: LanguageVariant[];
  state: CulturalSafetyState;
  awsLevel: "advice" | "watch_and_act" | "emergency_warning";
  onLanguageChange?: (id: LanguagePackId) => void;
  onElderApprovalRoute?: () => void;
  onIcOverride?: () => void;
}

const STATE_LABEL: Record<CulturalSafetyState, string> = {
  pending_elder: "Pending elder approval",
  approved: "Approved",
  declined: "Declined",
  timeout_lifesafety_override: "Timeout — IC override required",
  timeout_blocked: "Timeout — held, not published",
};

export function CulturalSafetyPanel(
  props: CulturalSafetyPanelProps,
): React.ReactElement {
  const {
    jurisdiction,
    variants,
    state,
    awsLevel,
    onLanguageChange,
    onElderApprovalRoute,
    onIcOverride,
  } = props;
  const available = React.useMemo(
    () => listAvailableLanguages(jurisdiction),
    [jurisdiction],
  );
  const [selected, setSelected] = React.useState<LanguagePackId>(
    available[0]?.id ?? "en",
  );
  const resolved = React.useMemo(
    () => resolveLanguageVariant(selected, variants),
    [selected, variants],
  );

  const handleSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value as LanguagePackId;
    setSelected(id);
    onLanguageChange?.(id);
  };

  const isOverrideEligible = awsLevel === "emergency_warning";

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="cultural-safety-panel"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Cultural safety</h2>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
          {STATE_LABEL[state]}
        </span>
      </header>

      <label className="block text-sm">
        Community language
        <select
          className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1"
          value={selected}
          onChange={handleSelect}
          data-testid="cultural-safety-language-select"
        >
          {available.map((p) => (
            <option key={p.id} value={p.id}>
              {p.display_name}
            </option>
          ))}
        </select>
      </label>

      <div
        className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-2 text-sm"
        data-testid="cultural-safety-resolved"
      >
        {resolved ? (
          <>
            <p className="font-mono text-xs text-slate-500">
              {resolved.language}
              {resolved.language !== selected ? " (fallback)" : ""}
            </p>
            <p>{resolved.text}</p>
          </>
        ) : (
          <p>No translation available — English will be used.</p>
        )}
      </div>

      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={onElderApprovalRoute}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          data-testid="cultural-safety-elder-route"
        >
          Route to elder
        </button>
        {state === "timeout_lifesafety_override" && isOverrideEligible ? (
          <button
            type="button"
            onClick={onIcOverride}
            className="rounded-md bg-rose-700 px-3 py-1.5 text-sm font-medium text-white"
            data-testid="cultural-safety-ic-override"
          >
            IC accept liability & override
          </button>
        ) : null}
      </div>
    </section>
  );
}

export default CulturalSafetyPanel;
