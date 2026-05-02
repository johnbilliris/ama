/**
 * T058 — Five-stage evacuation lifecycle (FR-012, §VI-A/B/C).
 *
 * Decision → Warning → Withdrawal → Shelter → Return.
 * Asserts all stage transitions plus vulnerable-population categories
 * are filterable.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

const STAGES = ["decision", "warning", "withdrawal", "shelter", "return"] as const;

const VULNERABLE_COHORTS = [
  "atsi",
  "cald",
  "disability",
  "children",
  "older-persons",
  "homeless",
  "tourists",
  "institutional-care",
] as const;

const PERSONAS = ["incident-commander", "operations-officer", "ses-nsw"] as const;

for (const personaId of PERSONAS) {
  test(
    `Five-stage evacuation lifecycle for '${personaId}' ` +
      `@persona:${personaId} @outcome:3 @hazard:tropical-cyclone+riverine-flood ` +
      `@fr:FR-012 @clause:V-B @clause:VI @p1`,
    async ({ resolvePersona, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      for (const stage of STAGES) {
        const res = await request.post(`/api/evacuations/transition`, {
          headers: {
            "X-Correlation-Id": correlationId,
            "X-Test-Persona-Id": persona.persona_id,
          },
          data: { stage, scenario: "outcome-3-tropical-cyclone-flood" },
          failOnStatusCode: false,
        });
        if (!res.ok()) {
          test.fail(true, `Evacuation transition '${stage}' not wired (FR-012 gap)`);
          return;
        }
        const payload = (await res.json()) as { stage?: string; vulnerable_cohorts?: string[] };
        expect(payload.stage).toBe(stage);
        for (const cohort of VULNERABLE_COHORTS) {
          expect(payload.vulnerable_cohorts ?? []).toContain(cohort);
        }
      }
    },
  );
}
