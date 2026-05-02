/**
 * T065 — Data source multiplicity (FR-018(a)).
 *
 * Each persona scenario surfaces ≥ 3 named data sources in COP/governance
 * views.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { GovernanceDataSourcePage } from "@web-coverage/_support/pages/governance.dataSource.po";

const PERSONAS = ["incident-commander", "planning-officer", "act-esa"] as const;

for (const personaId of PERSONAS) {
  test(
    `≥ 3 named data sources for '${personaId}' ` +
      `@persona:${personaId} @outcome:2 @hazard:bushfire+severe-storm ` +
      `@fr:FR-018 @clause:VIII @p1`,
    async ({ resolvePersona, page, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      await page.setExtraHTTPHeaders({
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      });
      const ds = new GovernanceDataSourcePage(page);
      await ds.goto();

      const res = await request.get("/api/governance/data-sources", {
        headers: { "X-Correlation-Id": correlationId, "X-Test-Persona-Id": persona.persona_id },
      });
      if (!res.ok()) {
        test.fail(true, "Data source endpoint not wired (FR-018 gap)");
        return;
      }
      const body = (await res.json()) as { sources?: Array<{ name: string }> };
      expect((body.sources ?? []).length).toBeGreaterThanOrEqual(3);
    },
  );
}
