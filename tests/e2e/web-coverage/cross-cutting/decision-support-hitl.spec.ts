/**
 * T064 — Decision-support HITL (FR-009, NN-#1, RISK-02).
 *
 * Every safety-critical action is gated by IC approval. Positive: approval
 * succeeds with operator identity logged. Negative: no approval = no
 * execution. HITL output is deterministic structured JSON.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

test(
  `Safety-critical action requires IC approval (positive) ` +
    `@persona:incident-commander @outcome:1 @hazard:bushfire+extreme-heat ` +
    `@fr:FR-009 @clause:NN-1 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("incident-commander");
    const res = await request.post("/api/decisions/safety-critical", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: { action: "issue-evacuation", approver_id: persona.persona_id, approved: true },
      failOnStatusCode: false,
    });
    if (!res.ok()) {
      test.fail(true, "Decision-support API not wired (FR-009 gap)");
      return;
    }
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.executed).toBe(true);
    expect(body.approver_id).toBe(persona.persona_id);
  },
);

test(
  `Safety-critical action without approval is rejected (negative) ` +
    `@persona:operations-officer @outcome:1 @hazard:bushfire+extreme-heat ` +
    `@fr:FR-009 @clause:NN-1 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("operations-officer");
    const res = await request.post("/api/decisions/safety-critical", {
      headers: {
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      },
      data: { action: "issue-evacuation", approved: false },
      failOnStatusCode: false,
    });
    if (res.status() === 404) {
      test.fail(true, "Decision-support API not wired (FR-009 gap)");
      return;
    }
    expect(res.status()).toBeGreaterThanOrEqual(400);
  },
);
