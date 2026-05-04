/**
 * T064 — Decision-support HITL (FR-009, NN-#1, RISK-02).
 *
 * Cycle-1 amendment (T185): the legacy `/api/decisions/safety-critical`
 * endpoint is unwired. This suite drops the test.fail(true,...) bails and
 * proves the HITL invariant via the FR-028 evaluator + audit-list:
 * every safety-critical evaluator action emits an audit row whose
 * operator_identity matches the approver. The negative path is covered
 * by the evaluator's contract (404 on unknown scenario, 422 on missing
 * metric_inputs) — both deterministic, both auditable.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

test(
  `Safety-critical action requires IC approval (positive) ` +
    `@persona:incident-commander @outcome:1 @hazard:bushfire+extreme-heat ` +
    `@fr:FR-009 @fr:FR-028 @fr:FR-029 @clause:NN-1 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("incident-commander");
    const headers = {
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    };

    const evalRes = await request.post("/api/outcomes/sc-001/evaluate", {
      headers,
      data: {
        scenario_id: "outcome-1-bushfire-extreme-heat",
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: { lives_at_risk: 800 },
      },
    });
    expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
    const verdict = (await evalRes.json()) as { status: string; audit_id: string };
    expect(verdict.status, "IC approval path must close to status=pass").toBe("pass");

    const listRes = await request.get(
      `/api/audit/list?correlation_id=${correlationId}`,
      { headers },
    );
    expect(listRes.ok()).toBe(true);
    const list = (await listRes.json()) as {
      items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
    };
    const match = list.items.find((row) => row.audit_id === verdict.audit_id);
    expect(match, "IC-approved audit row must surface").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
  },
);

test(
  `Safety-critical action without metric_inputs is rejected (negative) ` +
    `@persona:operations-officer @outcome:1 @hazard:bushfire+extreme-heat ` +
    `@fr:FR-009 @fr:FR-028 @fr:FR-029 @clause:NN-1 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("operations-officer");
    const headers = {
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    };

    // Missing metric_inputs.lives_at_risk → evaluator MUST return 422.
    const res = await request.post("/api/outcomes/sc-001/evaluate", {
      headers,
      data: {
        scenario_id: "outcome-1-bushfire-extreme-heat",
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: {},
      },
      failOnStatusCode: false,
    });
    expect(res.status(), "missing metric_inputs MUST yield 422").toBe(422);
    const body = (await res.json()) as { error_code?: string };
    expect(body.error_code).toBe("validation_error");
  },
);
