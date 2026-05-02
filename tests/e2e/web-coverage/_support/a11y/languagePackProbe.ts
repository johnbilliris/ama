/**
 * Language pack probe (T044).
 *
 * Confirms the FR-019 multilingual pack covers the languages declared in the
 * AWS warning payload by hitting `/api/i18n/coverage` and asserting set
 * containment.
 */
import type { APIRequestContext } from "@playwright/test";

export interface LanguagePackResult {
  ok: boolean;
  missing: string[];
}

export async function probeLanguagePack(
  request: APIRequestContext,
  requested: string[],
): Promise<LanguagePackResult> {
  const res = await request.get("/api/i18n/coverage");
  if (!res.ok()) {
    return { ok: false, missing: requested.slice() };
  }
  const body = (await res.json()) as { languages?: string[] };
  const supported = new Set(body.languages ?? []);
  const missing = requested.filter((l) => !supported.has(l));
  return { ok: missing.length === 0, missing };
}
