/**
 * T055 — COP refresh latency ≤ 5s (FR-008).
 *
 * Asserts the common operating picture refresh stays under SC-002 budget
 * across personas + AIIMS functions.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { IncidentsPage } from "@web-coverage/_support/pages/incidents.po";

const PERSONAS = [
  "incident-commander",
  "operations-officer",
  "planning-officer",
  "act-esa",
] as const;

for (const personaId of PERSONAS) {
  test(
    `COP refresh ≤ 5s for '${personaId}' ` +
      `@persona:${personaId} @outcome:2 @hazard:bushfire+severe-storm ` +
      `@fr:FR-008 @clause:II @p1`,
    async ({ resolvePersona, page, correlationId }) => {
      const persona = await resolvePersona(personaId);
      await page.setExtraHTTPHeaders({
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      });
      const incidents = new IncidentsPage(page);
      const start = Date.now();
      await incidents.goto();
      await expect(incidents.incidentList).toBeVisible({ timeout: 5000 });
      const elapsed = Date.now() - start;
      expect(elapsed, `COP refresh budget for ${personaId}`).toBeLessThanOrEqual(5000);
    },
  );
}
