/**
 * T148 — Capstone Outcome 3: 24-h-earlier evacuation.
 *
 * Proxy (SC-003): metric_inputs.evac_lead_hours ≥ 24h. Cycle-1
 * amendment (T186) drops the test.fail(true,...) bail and drives the
 * FR-028 evaluator + FR-029 audit-list contracts directly.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome3 from "@web-coverage/_support/fixtures/data/outcome-3-tropical-cyclone-flood.fixture.json";

test(
  `Capstone Outcome 3 closes — 24-h-earlier evacuation (SC-003) ` +
    `@persona:planning-officer @outcome:3 @hazard:tropical-cyclone+riverine-flood ` +
    `@fr:FR-016 @fr:FR-028 @fr:FR-029 @clause:VI @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("planning-officer");
    expect(outcome3.outcome).toBe(3);

    const evalRes = await request.post("/api/outcomes/sc-003/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: {
        scenario_id: "outcome-3-tropical-cyclone-flood",
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: { evac_lead_hours: 26 },
      },
    });
    expect(evalRes.ok(), `evaluator must respond 200; got ${evalRes.status()}`).toBe(true);
    const verdict = (await evalRes.json()) as {
      status: "pass" | "fail" | "gap";
      audit_id: string;
      metric_value: number;
      threshold: number;
    };
    expect(verdict.status, "SC-003 evac-lead-hours threshold must be satisfied").toBe("pass");
    expect(verdict.metric_value).toBeGreaterThanOrEqual(verdict.threshold);

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
      aiims_function: "planning",
      outcome: 3,
      hazard: "tropical-cyclone+riverine-flood",
      fr_id: "FR-016",
      constitution_clauses: ["VI"],
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
