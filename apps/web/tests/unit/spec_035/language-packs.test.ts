import { describe, expect, it } from "vitest";

import {
  LANGUAGE_PACKS,
  listAvailableLanguages,
  resolveLanguageVariant,
} from "../../../src/lib/i18n/language-packs";

describe("language packs (T050, FR-016 / NN-4)", () => {
  it("ships the v1 ATSI baseline + zh-Hans", () => {
    expect(Object.keys(LANGUAGE_PACKS)).toEqual(
      expect.arrayContaining([
        "en",
        "zh-Hans",
        "kimberley_pilbara",
        "palawa",
        "yolngu_matha",
        "pitjantjatjara",
        "warlpiri",
      ]),
    );
  });

  it("falls back to en when reviewer signature missing on ATSI variant", () => {
    const v = resolveLanguageVariant("yolngu_matha", [
      { language: "yolngu_matha", text: "draft", reviewer_signed: false },
      { language: "en", text: "english fallback" },
    ]);
    expect(v?.language).toBe("en");
    expect(v?.text).toBe("english fallback");
  });

  it("returns the primary variant when reviewer-signed", () => {
    const v = resolveLanguageVariant("yolngu_matha", [
      { language: "yolngu_matha", text: "approved", reviewer_signed: true },
      { language: "en", text: "english fallback" },
    ]);
    expect(v?.language).toBe("yolngu_matha");
  });

  it("zh-Hans does not require reviewer signature", () => {
    const v = resolveLanguageVariant("zh-Hans", [
      { language: "zh-Hans", text: "\u8b66\u544a" },
    ]);
    expect(v?.language).toBe("zh-Hans");
  });

  it("listAvailableLanguages includes en + AU + jurisdiction-scoped packs", () => {
    const wa = listAvailableLanguages("WA").map((p) => p.id);
    expect(wa).toEqual(expect.arrayContaining(["en", "zh-Hans", "kimberley_pilbara"]));
  });
});
