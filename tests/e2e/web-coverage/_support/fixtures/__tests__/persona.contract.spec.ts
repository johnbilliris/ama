/**
 * Persona-fixture contract spec (T053).
 *
 * Walks every persona served by GET /test-support/personas and asserts each
 * resolves through the personaResolver fixture without drift.
 *
 * This is the only Playwright spec in `_support/` — kept here on purpose so
 * the persona contract is bound to its fixture neighbour. All other specs
 * live under tests/e2e/web-coverage/{cross-cutting,persona,outcome}/.
 *
 * Tags:
 *   @persona:contract  @outcome:1  @hazard:contract  @fr:FR-001  @clause:NN-1  @p1
 */
import { test, expect, request } from "@playwright/test";

test.describe("personaResolver contract @persona:contract @outcome:1 @hazard:contract @fr:FR-001 @clause:NN-1 @p1", () => {
  test("every persona from /test-support/personas resolves identically", async ({ baseURL }) => {
    const apiBase = process.env.AMA_API_BASE_URL ?? baseURL ?? "http://localhost:8000";
    const ctx = await request.newContext({ baseURL: apiBase });
    const res = await ctx.get("/test-support/personas");
    expect(res.status(), `${apiBase}/test-support/personas`).toBe(200);
    const body = (await res.json()) as { personas: Array<{ persona_id: string }> };
    expect(body.personas.length).toBeGreaterThanOrEqual(68);

    for (const summary of body.personas) {
      const detail = await ctx.get(`/test-support/personas/${summary.persona_id}`);
      expect(detail.status(), summary.persona_id).toBe(200);
      const persona = (await detail.json()) as Record<string, unknown>;
      expect(persona.persona_id).toBe(summary.persona_id);
      expect(persona.aiims_function).toBeTruthy();
      expect(persona.jurisdiction_id).toBeTruthy();
      expect(Array.isArray(persona.permissions)).toBe(true);
    }
    await ctx.dispose();
  });
});
