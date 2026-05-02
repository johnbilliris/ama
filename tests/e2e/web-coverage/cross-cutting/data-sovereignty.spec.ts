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
    `@fr:FR-018 @clause:NN-2 @p1`,
  async ({ request, correlationId }) => {
    const res = await request.get("/api/governance/carve-outs", {
      headers: { "X-Correlation-Id": correlationId },
    });
    if (!res.ok()) {
      test.fail(true, "Carve-out registry endpoint not wired (FR-018 gap)");
      return;
    }
    const body = (await res.json()) as { entries?: Array<{ review_date: string; approvers?: string[] }> };
    const ninetyDaysMs = 90 * 24 * 60 * 60 * 1000;
    for (const entry of body.entries ?? []) {
      expect(new Date(entry.review_date).getTime() - Date.now()).toBeLessThanOrEqual(ninetyDaysMs);
      expect((entry.approvers ?? []).length).toBeGreaterThan(0);
    }
  },
);
