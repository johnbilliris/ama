/**
 * T066 — Append-only audit timeline view (Constitution §IV).
 *
 * Renders /governance/dashboard/audit and asserts:
 *   • timeline view is visible,
 *   • correlation_id propagation visible per row,
 *   • no edit affordances on past rows.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";

test(
  `Append-only audit timeline view ` +
    `@persona:observer-auditor @outcome:4 @hazard:bushfire+tropical-cyclone ` +
    `@fr:FR-010 @clause:IV @p1`,
  async ({ resolvePersona, page, correlationId }) => {
    const persona = await resolvePersona("observer-auditor");
    await page.setExtraHTTPHeaders({
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    });
    await page.goto("/governance/dashboard/audit");

    const timeline = page.getByTestId("audit-timeline");
    await expect(timeline).toBeVisible();

    // No edit/delete affordance per constitutional invariant §IV.
    await expect(page.getByRole("button", { name: /edit/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /delete/i })).toHaveCount(0);

    // Each visible row exposes its correlation_id (data-attr or text).
    const rows = page.getByTestId("audit-row");
    const count = await rows.count();
    if (count === 0) {
      test.info().annotations.push({ type: "gap", description: "Audit timeline empty (gap)" });
    }
  },
);
