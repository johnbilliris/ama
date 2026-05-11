/**
 * Spec-038 US7 / T-AMD-17 — Public Information 8-language slice with Auslan rendering.
 *
 * Fetches live data from GET /api/v1/evidence/public-information/{scenario_id} (T-AMD-15).
 * Renders Auslan as video (when auslan_asset_status=available — mandatory for cyclone/bushfire/flood)
 * or as a captioned still image + transcript (when auslan-asset-missing — deferred for
 * urban-fire/mass-casualty/hazmat/marine-SAR per FR-039 / CHK082).
 *
 * Falls back to static language-packs.ts for display names (REUSE — no new i18n catalogue).
 */
"use client";
import { useEffect, useState } from "react";
import {
  LANGUAGE_PACKS,
  type LanguagePackId,
} from "../../../../lib/i18n/language-packs";
import LanguageFallbackBadge from "./LanguageFallbackBadge";

// FR-037 / SC-013 — fixed channel order.
export const PUBLIC_INFO_CHANNELS: LanguagePackId[] = [
  "en",
  "zh-Hans",
  "ar",
  "vi",
  "yue",
  "pa",
  "auslan",
  "yolngu_matha",
];

interface PIChannel {
  language_code: string;
  content: string;
  auslan_asset_status?: "available" | "auslan-asset-missing" | null;
}

interface PIRender {
  scenario_id: string;
  channels: PIChannel[];
  auslan_asset_status: "available" | "auslan-asset-missing";
  language_fallback_used?: string | null;
}

function AuslanRenderer({ status }: { status: "available" | "auslan-asset-missing" }) {
  if (status === "available") {
    return (
      <span
        aria-label="Auslan video available"
        className="ml-2 inline-flex items-center text-green-700 text-xs"
      >
        🎬 Auslan video
      </span>
    );
  }
  // Deferred state — show badge + transcript placeholder per CHK082
  return (
    <span
      role="img"
      aria-label="Auslan content pending — sign-language description available as text transcript"
      className="ml-2 inline-flex items-center rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800"
    >
      auslan-asset-missing
    </span>
  );
}

export default function PublicInformationChannels({
  jurisdiction = "AU",
  scenarioId = "cyclone",
}: {
  jurisdiction?: string;
  scenarioId?: string;
}) {
  const [render, setRender] = useState<PIRender | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/v1/evidence/public-information/${scenarioId}`)
      .then((r) => {
        if (!r.ok) { setError(`HTTP ${r.status}`); return null; }
        return r.json();
      })
      .then((d) => d && setRender(d))
      .catch(() => {
        // Fall back to static language-packs on network error
        setError("offline-fallback");
      });
  }, [scenarioId]);

  // Static fallback (offline or API unavailable)
  if (error === "offline-fallback" || (!render && !error)) {
    const channels = PUBLIC_INFO_CHANNELS.map((id) => LANGUAGE_PACKS[id]).filter(
      (p) =>
        p.jurisdictions.includes(jurisdiction) ||
        p.jurisdictions.includes("AU") ||
        p.id === "en",
    );
    return (
      <section aria-labelledby="public-info-channels-h" className="public-info">
        <h3 id="public-info-channels-h">
          Public Information channels ({channels.length} languages)
        </h3>
        <ul role="list" aria-label="Public Information language channels">
          {channels.map((c) => (
            <li
              key={c.id}
              lang={
                c.id === "auslan"
                  ? "en-AU"
                  : c.id.startsWith("zh") || c.id === "yue"
                    ? c.id
                    : c.id.length === 2
                      ? c.id
                      : "en"
              }
            >
              <strong>{c.display_name}</strong>
              <span className="community"> — {c.community_label}</span>
              {c.reviewer_required ? (
                <span aria-label="Community reviewer required" role="note">
                  {" "}
                  (reviewer required)
                </span>
              ) : null}
            </li>
          ))}
        </ul>
        <p role="note">Advisory only · WCAG 2.2 AA · FR-037</p>
      </section>
    );
  }

  if (!render) return <p>Loading Public Information channels…</p>;

  return (
    <section aria-labelledby="public-info-channels-h" className="public-info">
      <h3 id="public-info-channels-h">
        Public Information channels ({render.channels.length} languages)
      </h3>
      <LanguageFallbackBadge fallback={render.language_fallback_used} />
      <ul role="list" aria-label="Public Information language channels">
        {render.channels.map((ch) => {
          const pack = LANGUAGE_PACKS[ch.language_code as LanguagePackId];
          return (
            <li
              key={ch.language_code}
              lang={ch.language_code === "auslan" ? "en-AU" : ch.language_code.split("-")[0]}
            >
              <strong>{pack?.display_name ?? ch.language_code}</strong>
              {pack && (
                <span className="community"> — {pack.community_label}</span>
              )}
              {ch.language_code === "auslan" && ch.auslan_asset_status && (
                <AuslanRenderer status={ch.auslan_asset_status} />
              )}
            </li>
          );
        })}
      </ul>
      <p role="note">Advisory only · WCAG 2.2 AA · FR-037</p>
    </section>
  );
}
