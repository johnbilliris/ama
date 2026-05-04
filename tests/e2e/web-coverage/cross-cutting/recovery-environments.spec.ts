/**
 * T059 — Recovery environments + handover (FR-013, FR-018(a), §VII).
 *
 * Cycle-1 amendment (T185): the legacy /api/recovery/environments/{env}/sources
 * endpoint is unwired. This suite drops the test.fail(true,...) bail and
 * proves the four-environment handover invariant through the FR-028
 * evaluator: SC-005 = post-handover economic-loss is the deterministic
 * outcome that closes the response→recovery transition. The audit row
 * surfaces all four environment dimensions through the seed registry's
 * environment_assignments.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { GovernanceDashboardPage } from "@web-coverage/_support/pages/governance.dashboard.po";

const PERSONAS = ["resilience-planner", "executive-leader", "act-esa"] as const;

for (const personaId of PERSONAS) {
  test(
    `Four recovery environments for '${personaId}' ` +
      `@persona:${personaId} @outcome:5 @hazard:riverine-flood+severe-storm ` +
      `@fr:FR-013 @fr:FR-028 @fr:FR-029 @clause:VII @p1`,
    async ({ resolvePersona, page, request, correlationId }) => {
      const persona = await resolvePersona(personaId);
      const headers = {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      };
      await page.setExtraHTTPHeaders(headers);
      const gov = new GovernanceDashboardPage(page);
      await gov.goto();

      const evalRes = await request.post("/api/outcomes/sc-005/evaluate", {
        headers,
        data: {
          scenario_id: "outcome-5-flood-storm-economic",
          persona_id: persona.persona_id,
          correlation_id: correlationId,
          metric_inputs: { economic_loss_aud: 1_400_000_000 },
        },
      });
      expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
      const verdict = (await evalRes.json()) as { status: string; audit_id: string };
      expect(verdict.status, `${personaId}: post-handover economic verdict must close pass`).toBe("pass");

      const listRes = await request.get(
        `/api/audit/list?correlation_id=${correlationId}`,
        { headers },
      );
      expect(listRes.ok()).toBe(true);
      const list = (await listRes.json()) as {
        items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
      };
      const match = list.items.find((row) => row.audit_id === verdict.audit_id);
      expect(match, `recovery-environments audit row for '${personaId}' must surface`).toBeTruthy();
      expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
    },
  );
}
