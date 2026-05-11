/**
 * PIO AWS Composer panel (T037, FR-002).
 *
 * AWS-level selector, hazard / location / action, community-language picker
 * (Simplified Chinese + ATSI placeholder), in-page accessibility scan invocation,
 * IC-approval submission. Solicits the `communication-agent` via the existing
 * MAF runtime endpoint to draft multilingual variants.
 */

"use client";

import * as React from "react";

import {
  listAvailableLanguages,
  type LanguagePack,
} from "../../../../lib/i18n/language-packs";

const AWS_LEVELS = ["Advice", "Watch and Act", "Emergency Warning"] as const;
type AwsLevel = (typeof AWS_LEVELS)[number];

interface DraftVariant {
  language: string;
  text: string;
  reviewer_required: boolean;
}

export interface PioAwsComposerProps {
  endpointBase?: string;
  /**
   * Jurisdiction code (e.g. `WA`, `NT`, `TAS`) used to filter the offered
   * community-language pack list (NN-4 v1 baseline). Defaults to `AU` so the
   * Simplified-Chinese baseline is always available on the public-bulletin
   * surface (spec-035 T073 / FR-016 / FR-029).
   */
  jurisdiction?: string;
  onApprovalRequest?: (payload: { variants: DraftVariant[] }) => void;
}

export function PioAwsComposer(props: PioAwsComposerProps): React.ReactElement {
  const { endpointBase = "/api", jurisdiction = "AU", onApprovalRequest } = props;
  const availableLanguages = React.useMemo<LanguagePack[]>(
    () => listAvailableLanguages(jurisdiction),
    [jurisdiction],
  );
  const [level, setLevel] = React.useState<AwsLevel>("Advice");
  const [hazard, setHazard] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [action, setAction] = React.useState("");
  const [languages, setLanguages] = React.useState<string[]>(["en"]);
  const [variants, setVariants] = React.useState<DraftVariant[]>([]);
  const [drafting, setDrafting] = React.useState(false);
  const [a11yResult, setA11yResult] = React.useState<string | null>(null);
  const [err, setErr] = React.useState<string | null>(null);

  const draft = async () => {
    setDrafting(true);
    setErr(null);
    try {
      const res = await fetch(`${endpointBase}/agents/communication/draft-aws`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          level,
          hazard,
          location,
          action,
          languages,
        }),
      });
      if (!res.ok) throw new Error(`draft-failed:${res.status}`);
      const body = (await res.json()) as { variants: DraftVariant[] };
      setVariants(body.variants);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setDrafting(false);
    }
  };

  const runA11y = async () => {
    if (typeof window === "undefined") return;
    try {
      const dynamicImport = new Function(
        "m",
        "return import(m)",
      ) as (m: string) => Promise<unknown>;
      const mod = (await dynamicImport("axe-core")) as {
        default: {
          run: (
            n: Element,
            opts: unknown,
          ) => Promise<{ violations: { id: string }[] }>;
        };
      };
      const result = await mod.default.run(document.body, {
        runOnly: ["wcag2a", "wcag2aa"],
      });
      const issues = result.violations.length;
      setA11yResult(
        issues === 0
          ? "WCAG 2.1 AA: 0 violations"
          : `WCAG 2.1 AA: ${issues} violations — ${result.violations
              .map((v: { id: string }) => v.id)
              .join(", ")}`,
      );
    } catch (e) {
      setA11yResult(
        `axe-core unavailable: ${e instanceof Error ? e.message : String(e)}`,
      );
    }
  };

  const requestApproval = () => {
    onApprovalRequest?.({ variants });
  };

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="pio-aws-composer"
    >
      <h2 className="mb-3 text-lg font-semibold">Australian Warning System composer</h2>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <label className="text-sm">
          AWS level
          <select
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1"
            value={level}
            onChange={(e) => setLevel(e.target.value as AwsLevel)}
          >
            {AWS_LEVELS.map((l) => (
              <option key={l}>{l}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Hazard
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1"
            value={hazard}
            onChange={(e) => setHazard(e.target.value)}
          />
        </label>
        <label className="text-sm">
          Location
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
        </label>
        <label className="text-sm">
          Recommended action
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1"
            value={action}
            onChange={(e) => setAction(e.target.value)}
          />
        </label>
      </div>
      <fieldset className="mt-3 text-sm">
        <legend className="font-medium">Community languages</legend>
        {availableLanguages.map((l) => (
          <label key={l.id} className="mr-3 inline-flex items-center gap-1">
            <input
              type="checkbox"
              checked={languages.includes(l.id)}
              onChange={(e) =>
                setLanguages((prev) =>
                  e.target.checked
                    ? [...prev, l.id]
                    : prev.filter((c) => c !== l.id),
                )
              }
              data-testid={`pio-language-toggle-${l.id}`}
            />
            {l.display_name}
            {l.reviewer_required ? (
              <span
                className="ml-1 rounded bg-amber-100 px-1 text-[10px] font-medium uppercase tracking-wide text-amber-900"
                title="Community-reviewer signature required"
              >
                reviewer
              </span>
            ) : null}
          </label>
        ))}
      </fieldset>

      <div className="mt-3 flex gap-2">
        <button
          type="button"
          disabled={drafting}
          onClick={draft}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {drafting ? "Drafting…" : "Draft variants"}
        </button>
        <button
          type="button"
          onClick={runA11y}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          Run accessibility scan
        </button>
        <button
          type="button"
          disabled={variants.length === 0}
          onClick={requestApproval}
          className="rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          Request IC approval
        </button>
      </div>

      {a11yResult ? (
        <p className="mt-2 text-xs text-slate-700" role="status">
          {a11yResult}
        </p>
      ) : null}
      {err ? (
        <p className="mt-2 text-sm text-rose-700" role="alert">
          {err}
        </p>
      ) : null}

      {variants.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {variants.map((v) => (
            <li
              key={v.language}
              className="rounded-md border border-slate-200 p-2 text-sm"
            >
              <p className="font-mono text-xs text-slate-500">{v.language}</p>
              <p>{v.text}</p>
              {v.reviewer_required ? (
                <p className="text-xs text-amber-700">
                  Community reviewer required before publish.
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

export default PioAwsComposer;
