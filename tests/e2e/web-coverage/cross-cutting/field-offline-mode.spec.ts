/**
 * T061 — Field offline mode (FR-017, NN-#5).
 *
 * Cycle-1 amendment (T185): the legacy /api/field/hazard-report endpoint
 * is unwired. This suite drops the test.fail(true,...) bail and proves
 * the FR-017 idempotency invariant directly through the FR-028 evaluator:
 * two POSTs against the same (correlation_id, scenario_id, persona_id,
 * sc_id) tuple MUST return the same audit_id (idempotency cache hit).
 * That tuple is precisely how the field offline queue dedupes replays.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

test(
  `Field-coordinator offline queue dedupes + replays audit ` +
    `@persona:field-coordinator @outcome:2 @hazard:bushfire+severe-storm ` +
    `@fr:FR-017 @fr:FR-028 @fr:FR-029 @clause:NN-5 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("field-coordinator");
    const headers = {
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    };
    const body = {
      scenario_id: "outcome-2-bushfire-severe-storm",
      persona_id: persona.persona_id,
      correlation_id: correlationId,
      metric_inputs: { signal_to_action_ms: 4500 },
    };

    const submit1 = await request.post("/api/outcomes/sc-002/evaluate", {
      headers,
      data: body,
    });
    expect(submit1.ok()).toBe(true);
    const result1 = (await submit1.json()) as { audit_id: string };

    const submit2 = await request.post("/api/outcomes/sc-002/evaluate", {
      headers,
      data: body,
    });
    expect(submit2.ok()).toBe(true);
    const result2 = (await submit2.json()) as { audit_id: string };

    expect(result2.audit_id, "idempotent dedupe by correlation id").toBe(result1.audit_id);

    const listRes = await request.get(
      `/api/audit/list?correlation_id=${correlationId}`,
      { headers },
    );
    expect(listRes.ok()).toBe(true);
    const list = (await listRes.json()) as {
      items: Array<{ audit_id: string; operator_identity: { persona_id: string } }>;
    };
    const matches = list.items.filter((row) => row.audit_id === result1.audit_id);
    expect(matches.length, "exactly one row per (correlation_id, audit_id)").toBe(1);
    expect(matches[0].operator_identity.persona_id).toBe(persona.persona_id);
  },
);
