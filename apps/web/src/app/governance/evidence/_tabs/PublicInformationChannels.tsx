"use client";

import type { PublicInformationRender } from "@ama/domain";
import { useCallback, useEffect, useState } from "react";
import { getPublicInformation } from "../../../../lib/api/evidence";
import { LANGUAGE_PACKS, type LanguagePackId } from "../../../../lib/i18n/language-packs";
import LanguageFallbackBadge from "./LanguageFallbackBadge";

const SCENARIOS = [
  "bushfire",
  "flood",
  "cyclone",
  "urban_fire",
  "mass_casualty",
  "hazmat",
  "marine_sar",
] as const;
const LANGUAGES = ["en-AU", "zh-Hans", "ar", "vi", "yue", "pa", "auslan", "yolngu_matha"] as const;

export default function PublicInformationChannels() {
  const [scenarioId, setScenarioId] = useState<string>("cyclone");
  const [language, setLanguage] = useState<string>("en-AU");
  const [render, setRender] = useState<PublicInformationRender | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    (signal?: AbortSignal) => {
      setLoading(true);
      setError("");
      void getPublicInformation(scenarioId, language, signal)
        .then(setRender)
        .catch((reason: unknown) => {
          if ((reason as Error).name !== "AbortError") setError(String(reason));
        })
        .finally(() => setLoading(false));
    },
    [language, scenarioId],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  return (
    <div data-testid="evidence-public-information-tab">
      <div className="mb-4 flex flex-wrap gap-4">
        <label>
          Scenario{" "}
          <select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>
            {SCENARIOS.map((scenario) => (
              <option key={scenario} value={scenario}>{scenario.replaceAll("_", " ")}</option>
            ))}
          </select>
        </label>
        <label>
          Requested language{" "}
          <select value={language} onChange={(event) => setLanguage(event.target.value)}>
            {LANGUAGES.map((code) => (
              <option key={code} value={code}>{LANGUAGE_PACKS[code]?.display_name ?? code}</option>
            ))}
          </select>
        </label>
      </div>
      {loading ? <p role="status">Loading public information…</p> : null}
      {error ? (
        <div role="alert">
          <p>Failed to load public information: {error}</p>
          <button type="button" onClick={() => load()}>Retry</button>
        </div>
      ) : null}
      {render ? (
        <section className="public-info" aria-label="Public information channels">
          {render.auslan_asset_missing ? (
            <p role="status">auslan-asset-missing · manual</p>
          ) : null}
          {render.auslan ? (
            <figure>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={render.auslan.captioned_image_url}
                alt={`${scenarioId.replaceAll("_", " ")} Auslan transcript placeholder`}
              />
              <figcaption>{render.auslan.transcript}</figcaption>
            </figure>
          ) : null}
          <ul role="list">
            {render.channels.map((channel) => {
              const pack = LANGUAGE_PACKS[channel.language_code as LanguagePackId];
              return (
                <li key={channel.language_code} lang={channel.language_code.split("-")[0]}>
                  <h3>{pack?.display_name ?? channel.language_code}</h3>
                  <LanguageFallbackBadge fallback={channel.language_fallback_used} />
                  {channel.provenance === "manual" ? <span role="status">manual</span> : null}
                  <p>{channel.body}</p>
                  {channel.fk_grade != null ? <p>Readability grade: {channel.fk_grade}</p> : null}
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
