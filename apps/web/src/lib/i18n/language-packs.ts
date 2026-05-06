/**
 * Language pack registry (T050, FR-016 / NN-4 v1).
 *
 * Provides ATSI community-language packs and a fallback chain renderer
 * used by the PIO composer and every cultural-safety surface.
 *
 * Per Clarifications Q5 + research.md R-010, the v1 baseline ships:
 * `kimberley_pilbara`, `palawa`, `yolngu_matha`, `pitjantjatjara`, `warlpiri`,
 * plus `zh-Hans` (Simplified Chinese) for the public-bulletin surface.
 */

export type LanguagePackId =
  | "en"
  | "zh-Hans"
  | "kimberley_pilbara"
  | "palawa"
  | "yolngu_matha"
  | "pitjantjatjara"
  | "warlpiri";

export interface LanguagePack {
  id: LanguagePackId;
  display_name: string;
  community_label: string;
  jurisdictions: string[];
  /** Fallback chain when no community-reviewed translation is available. */
  fallback_chain: LanguagePackId[];
  reviewer_required: boolean;
}

export const LANGUAGE_PACKS: Readonly<Record<LanguagePackId, LanguagePack>> =
  Object.freeze({
    en: {
      id: "en",
      display_name: "English",
      community_label: "English",
      jurisdictions: ["AU"],
      fallback_chain: [],
      reviewer_required: false,
    },
    "zh-Hans": {
      id: "zh-Hans",
      display_name: "\u7b80\u4f53\u4e2d\u6587 (Simplified Chinese)",
      community_label: "Simplified Chinese",
      jurisdictions: ["AU"],
      fallback_chain: ["en"],
      reviewer_required: false,
    },
    kimberley_pilbara: {
      id: "kimberley_pilbara",
      display_name: "Kimberley / Pilbara languages",
      community_label: "Kimberley / Pilbara",
      jurisdictions: ["WA"],
      fallback_chain: ["en"],
      reviewer_required: true,
    },
    palawa: {
      id: "palawa",
      display_name: "palawa kani",
      community_label: "palawa kani",
      jurisdictions: ["TAS"],
      fallback_chain: ["en"],
      reviewer_required: true,
    },
    yolngu_matha: {
      id: "yolngu_matha",
      display_name: "Yol\u014bu Matha",
      community_label: "Yolngu Matha",
      jurisdictions: ["NT"],
      fallback_chain: ["en"],
      reviewer_required: true,
    },
    pitjantjatjara: {
      id: "pitjantjatjara",
      display_name: "Pitjantjatjara",
      community_label: "Pitjantjatjara",
      jurisdictions: ["SA", "NT", "WA"],
      fallback_chain: ["en"],
      reviewer_required: true,
    },
    warlpiri: {
      id: "warlpiri",
      display_name: "Warlpiri",
      community_label: "Warlpiri",
      jurisdictions: ["NT"],
      fallback_chain: ["en"],
      reviewer_required: true,
    },
  });

export interface LanguageVariant {
  language: LanguagePackId;
  text: string;
  reviewer_signed?: boolean;
}

/**
 * Resolves the first variant in the fallback chain for `requested`. If the
 * primary variant has no community reviewer signature and a reviewer is
 * required, the renderer returns the next available variant (typically `en`).
 */
export function resolveLanguageVariant(
  requested: LanguagePackId,
  variants: LanguageVariant[],
): LanguageVariant | null {
  const pack = LANGUAGE_PACKS[requested];
  if (!pack) return null;
  const primary = variants.find((v) => v.language === requested);
  if (primary && (!pack.reviewer_required || primary.reviewer_signed)) {
    return primary;
  }
  for (const fallback of pack.fallback_chain) {
    const v = variants.find((vv) => vv.language === fallback);
    if (v) return v;
  }
  return null;
}

export function listAvailableLanguages(jurisdiction: string): LanguagePack[] {
  return Object.values(LANGUAGE_PACKS).filter(
    (p) =>
      p.jurisdictions.includes(jurisdiction) ||
      p.jurisdictions.includes("AU") ||
      p.id === "en",
  );
}
