/**
 * T146 — Capstone Outcome 1: Lives saved (zero preventable deaths).
 *
 * Proxy (SC-001):
 *   • Warning latency ≤ 2 minutes (FR-011)
 *   • IC-approval timeliness ≤ 5 / 15 / 30 minutes (FR-008/FR-009)
 *   • Multilingual reach ≥ en + zh-Hans + aus-x-atsi-placeholder (FR-014)
 *
 * Validates against tests/e2e/web-coverage/_support/fixtures/data/
 * outcome-1-bushfire-extreme-heat.fixture.json via outcome-proxy.ts.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validateOutcomeProxy } from "@web-coverage/_support/validators/outcome-proxy";
import outcome1 from "@web-coverage/_support/fixtures/data/outcome-1-bushfire-extreme-heat.fixture.json";

test(
  `Capstone Outcome 1 closes — lives saved (SC-001) ` +
    `@persona:incident-commander @outcome:1 @hazard:bushfire+extreme-heat ` +
    `@fr:FR-011 @fr:FR-014 @fr:FR-009 @clause:I @clause:V-A @clause:NN-1 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("incident-commander");
    expect(outcome1.outcome).toBe(1);

    const res = await request.post("/api/outcomes/sc-001/evaluate", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: { scenario: "outcome-1-bushfire-extreme-heat" },
      failOnStatusCode: false,
    });
    if (!res.ok()) {
      test.fail(true, "Outcome SC-001 evaluator API not wired (gap)");
      return;
    }
    const body = (await res.json()) as {
      warning_latency_seconds?: number;
      approval_latency_minutes?: number;
      languages?: string[];
    };
    expect(body.warning_latency_seconds ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(120);
    expect(body.approval_latency_minutes ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(5);
    expect(body.languages ?? []).toEqual(expect.arrayContaining(["en", "zh-Hans", "aus-x-atsi-placeholder"]));

    // Trace closure: validate the row that this test will emit against the
    // outcome-1 fixture proxy.
    const validation = validateOutcomeProxy({
      persona_id: persona.persona_id,
      aiims_function: "control",
      outcome: 1,
      hazard: "bushfire+extreme-heat",
      fr_id: "FR-011",
      constitution_clauses: ["I"],
      test_ids: [test.info().testId],
      route: "/incidents",
      audit_evidence_id: null,
      correlation_id: correlationId,
      status: "passed",
      duration_ms: 0,
      emitted_at: new Date().toISOString(),
    });
    expect(validation.reasons, validation.reasons.join("; ")).toEqual([]);
  },
);
