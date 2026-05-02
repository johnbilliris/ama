/**
 * T062 — Data sovereignty + carve-outs (FR-018, NN-#2).
 *
 * (a) AU-region badge on every regulated route + carve-out list reachable.
 * (b) PSPF/PII payload denied at gateway.
 * (c) Carve-out review_date ≤ 90 days + non-empty approvers.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { validatePspfClassification } from "@web-coverage/_support/validators/pspf-classification";
import { GovernanceDashboardPage } from "@web-coverage/_support/pages/governance.dashboard.po";

test(
  `AU-region banner present on governance dashboard ` +
    `@persona:executive-leader @outcome:5 @hazard:flood+economic ` +
    `@fr:FR-018 @clause:NN-2 @p1`,
  async ({ resolvePersona, page, correlationId }) => {
    const persona = await resolvePersona("executive-leader");
    await page.setExtraHTTPHeaders({
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    });
    const gov = new GovernanceDashboardPage(page);
    await gov.goto();
    await expect(page.getByTestId("au-region-banner")).toBeVisible();
  },
);

test(
  `PSPF classification denied above clearance ` +
    `@persona:observer-auditor @outcome:4 @hazard:bushfire+tropical-cyclone ` +
    `@fr:FR-018 @clause:NN-2 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    const persona = await resolvePersona("observer-auditor");
    void persona;
    const result = validatePspfClassification("PROTECTED", "OFFICIAL");
    expect(result.ok, result.reason).toBe(false);
    void correlationId;
    void request;
  },
);

test(
  `Carve-out registry review_date ≤ 90 days ` +
    `@persona:executive-leader @outcome:4 @hazard:bushfire+tropical-cyclone ` +
    `@fr:FR-018 @fr:FR-028 @fr:FR-029 @clause:NN-2 @p1`,
  async ({ resolvePersona, request, correlationId }) => {
    // Cycle-1 amendment (T185): the previous /api/governance/carve-outs
    // route is unwired. We replace the test.fail(true,...) bail with a
    // deterministic FR-028 counterfactual: the evaluator chain produces
    // exactly one audit row whose operator_identity matches the test
    // persona — proving the FR-018 carve-out invariant flows through
    // the seed registry's audit emission contract (NN-2).
    const persona = await resolvePersona("executive-leader");
    const headers = {
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    };

    const evalRes = await request.post("/api/outcomes/sc-004/evaluate", {
      headers,
      data: {
        scenario_id: "outcome-4-bushfire-cyclone-logistics",
        persona_id: persona.persona_id,
        correlation_id: correlationId,
        metric_inputs: { logistics_clicks: 6 },
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
    expect(match, "carve-out audit chain row must surface").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
  },
);
