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
  | "en-AU"
  | "en"
  | "zh-Hans"
  | "ar"
  | "vi"
  | "yue"
  | "pa"
  | "auslan"
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
    "en-AU": {
      id: "en-AU",
      display_name: "English (Australia)",
      community_label: "English (Australia)",
      jurisdictions: ["AU"],
      fallback_chain: ["en"],
      reviewer_required: false,
    },
    en: {
      id: "en",
      display_name: "English",
      community_label: "English",
      jurisdictions: ["AU"],
      fallback_chain: ["en-AU"],
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
    // Spec-038 US7 (FR-037 / SC-013) — additional ABS-Census language channels
    // for the Public Information KPI 8-language render. Reuses the same registry
    // — no new i18n catalogue introduced.
    ar: {
      id: "ar",
      display_name: "\u0627\u0644\u0639\u0631\u0628\u064a\u0629 (Arabic)",
      community_label: "Arabic",
      jurisdictions: ["AU"],
      fallback_chain: ["en"],
      reviewer_required: false,
    },
    vi: {
      id: "vi",
      display_name: "Ti\u1ebfng Vi\u1ec7t (Vietnamese)",
      community_label: "Vietnamese",
      jurisdictions: ["AU"],
      fallback_chain: ["en"],
      reviewer_required: false,
    },
    yue: {
      id: "yue",
      display_name: "\u7cb5\u8a9e (Cantonese)",
      community_label: "Cantonese",
      jurisdictions: ["AU"],
      fallback_chain: ["zh-Hans", "en"],
      reviewer_required: false,
    },
    pa: {
      id: "pa",
      display_name: "\u0a2a\u0a70\u0a1c\u0a3e\u0a2c\u0a40 (Punjabi)",
      community_label: "Punjabi",
      jurisdictions: ["AU"],
      fallback_chain: ["en"],
      reviewer_required: false,
    },
    auslan: {
      id: "auslan",
      display_name: "Auslan (Australian Sign Language)",
      community_label: "Auslan",
      jurisdictions: ["AU"],
      fallback_chain: ["en"],
      reviewer_required: true,
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
