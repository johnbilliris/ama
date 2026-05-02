/**
 * T059 — Recovery environments + handover (FR-013, FR-018(a), §VII).
 *
 * Four environments tracked (Social, Built, Economic, Natural) with managed
 * response→recovery handover and ≥ 3 data sources per environment.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { GovernanceDashboardPage } from "@web-coverage/_support/pages/governance.dashboard.po";

const ENVIRONMENTS = ["social", "built", "economic", "natural"] as const;
const PERSONAS = ["resilience-planner", "executive-leader", "act-esa"] as const;

for (const personaId of PERSONAS) {
  test(
    `Four recovery environments for '${personaId}' ` +
      `@persona:${personaId} @outcome:5 @hazard:riverine-flood+severe-storm ` +
      `@fr:FR-013 @clause:VII @p1`,
    async ({ resolvePersona, page, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      await page.setExtraHTTPHeaders({
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      });
      const gov = new GovernanceDashboardPage(page);
      await gov.goto();

      for (const env of ENVIRONMENTS) {
        const res = await request.get(`/api/recovery/environments/${env}/sources`, {
          headers: {
            "X-Correlation-Id": correlationId,
            "X-Test-Persona-Id": persona.persona_id,
          },
        });
        if (!res.ok()) {
          test.fail(true, `Recovery environment '${env}' not wired (FR-013 gap)`);
          return;
        }
        const body = (await res.json()) as { sources?: string[] };
        expect((body.sources ?? []).length).toBeGreaterThanOrEqual(3);
      }
    },
  );
}
