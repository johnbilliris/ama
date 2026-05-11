/**
 * Spec-038 US7 — Public Information 8-language slice (T-A13 / T-A14).
 *
 * Iterates the existing `language-packs.ts` registry (REUSE — no new i18n
 * catalogue) to render the 8 mandated channels for the Public Information
 * KPI render: English plain-Grade-8 + Mandarin + Arabic + Vietnamese +
 * Cantonese + Punjabi + Auslan + ≥1 jurisdiction-appropriate First-Nations
 * language. WCAG 2.2 AA semantics applied: lang attributes, role="list",
 * aria-labels.
 */
import {
  LANGUAGE_PACKS,
  type LanguagePackId,
} from "../../../../lib/i18n/language-packs";

// FR-037 / SC-013 — fixed channel order so the render is deterministic.
export const PUBLIC_INFO_CHANNELS: LanguagePackId[] = [
  "en",
  "zh-Hans",
  "ar",
  "vi",
  "yue",
  "pa",
  "auslan",
  // First-Nations slot — picked deterministically by jurisdiction filter.
  "yolngu_matha",
];

export default function PublicInformationChannels({
  jurisdiction = "AU",
}: {
  jurisdiction?: string;
}) {
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
