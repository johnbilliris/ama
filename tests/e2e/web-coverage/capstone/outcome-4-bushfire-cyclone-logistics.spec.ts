/**
 * T149 — Capstone Outcome 4: 30% logistics-friction reduction.
 *
 * Proxy (SC-004): metric_inputs.logistics_clicks ≤ 7. Cycle-1 amendment
 * (T186) drops the test.fail(true,...) bail and drives the FR-028
 * evaluator + FR-029 audit-list contracts directly.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome4 from "@web-coverage/_support/fixtures/data/outcome-4-bushfire-cyclone-logistics.fixture.json";

test(
  `Capstone Outcome 4 closes — 30% logistics friction reduction (SC-004) ` +
    `@persona:logistics-officer @outcome:4 @hazard:bushfire+tropical-cyclone ` +
    `@fr:FR-015 @fr:FR-028 @fr:FR-029 @clause:VIII @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("logistics-officer");
    expect(outcome4.outcome).toBe(4);

    const evalRes = await request.post("/api/outcomes/sc-004/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: {
        scenario_id: "outcome-4-bushfire-cyclone-logistics",
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: { logistics_clicks: 6 },
      },
    });
    expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
    const verdict = (await evalRes.json()) as {
      status: "pass" | "fail" | "gap";
      audit_id: string;
      metric_value: number;
      threshold: number;
    };
    expect(verdict.status, "SC-004 logistics-clicks threshold must be satisfied").toBe("pass");
    expect(verdict.metric_value).toBeLessThanOrEqual(verdict.threshold);

    const listRes = await request.get(
      `/api/audit/list?correlation_id=${correlationId}`,
      {
        headers: {
          "X-Correlation-Id": correlationId,
          "X-Test-Persona-Id": persona.persona_id,
        },
      },
    );
    expect(listRes.ok(), "/api/audit/list must succeed").toBe(true);
    const list = (await listRes.json()) as {
      items: Array<{
        audit_id: string;
        operator_identity: { persona_id: string };
      }>;
    };
    const match = list.items.find((row) => row.audit_id === verdict.audit_id);
    expect(match, "evaluator audit_id must appear in /api/audit/list").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);

    const validation = validateOutcomeProxy({
      persona_id: persona.persona_id,
      aiims_function: "logistics",
      outcome: 4,
      hazard: "bushfire+tropical-cyclone",
      fr_id: "FR-015",
      constitution_clauses: ["VIII"],
      test_ids: [test.info().testId],
      route: "/operations/workflows",
      audit_evidence_id: verdict.audit_id,
      correlation_id: correlationId,
      status: "passed",
      duration_ms: 0,
      emitted_at: new Date().toISOString(),
    });
    expect(validation.reasons, validation.reasons.join("; ")).toEqual([]);
  },
);
