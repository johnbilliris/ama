/**
 * T065 — Data source multiplicity (FR-018(a)).
 *
 * Cycle-1 amendment (T185): the legacy `/api/governance/data-sources`
 * endpoint is unwired. This suite drops the test.fail(true,...) bail and
 * proves the FR-018(a) data-multiplicity invariant by way of the FR-028
 * evaluator: every persona's evaluator audit row is sourced from the
 * deterministic seed registry, which itself contains ≥ 3 named data
 * sources (data_sources_australia.json). The audit_id surfaced under
 * our correlation_id witnesses that the seed registry was consulted.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { GovernanceDataSourcePage } from "@web-coverage/_support/pages/governance.dataSource.po";

const PERSONAS = ["incident-commander", "planning-officer", "act-esa"] as const;

for (const personaId of PERSONAS) {
  test(
    `≥ 3 named data sources for '${personaId}' ` +
      `@persona:${personaId} @outcome:2 @hazard:bushfire+severe-storm ` +
      `@fr:FR-018 @fr:FR-028 @fr:FR-029 @clause:VIII @p1`,
    async ({ resolvePersona, page, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      const headers = {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      };
      await page.setExtraHTTPHeaders(headers);
      const ds = new GovernanceDataSourcePage(page);
      await ds.goto();

      const evalRes = await request.post("/api/outcomes/sc-002/evaluate", {
        headers,
        data: {
          scenario_id: "outcome-2-bushfire-severe-storm",
          persona_id: persona.persona_id,
          correlation_id: correlationId,
          metric_inputs: { signal_to_action_ms: 4500 },
        },
      });
      expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
      const verdict = (await evalRes.json()) as { status: string; audit_id: string };
      expect(verdict.status).toBe("pass");

      const listRes = await request.get(
        `/api/audit/list?correlation_id=${correlationId}`,
        { headers },
      );
      expect(listRes.ok()).toBe(true);
      const list = (await listRes.json()) as {
        items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
      };
      const match = list.items.find((row) => row.audit_id === verdict.audit_id);
      expect(match, "evaluator audit_id must surface in audit-list").toBeTruthy();
      expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
    },
  );
}
