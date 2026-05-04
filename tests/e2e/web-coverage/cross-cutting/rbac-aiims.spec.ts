/**
 * T054 — RBAC AIIMS function map (cross-cutting US2).
 *
 * Asserts FR-007 + Constitution §II-A:
 *   • Control role MAY approve a cross-agency action.
 *   • Logistics role MUST NOT approve an evacuation order.
 *
 * Parameterised over ≥ 3 personas drawn from ≥ 3 jurisdictions per
 * spec §User Story 2.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { IncidentsPage } from "@web-coverage/_support/pages/incidents.po";
import { WorkspacesPage } from "@web-coverage/_support/pages/workspaces.po";

const POSITIVE = [
  { persona: "incident-commander", jurisdiction: "operational" },
  { persona: "act-esa", jurisdiction: "act" },
  { persona: "nema", jurisdiction: "commonwealth" },
] as const;

const NEGATIVE = [
  { persona: "logistics-officer", jurisdiction: "operational" },
  { persona: "arc", jurisdiction: "cross-sector" },
  { persona: "transport", jurisdiction: "cross-sector" },
] as const;

for (const row of POSITIVE) {
  test(
    `Control persona '${row.persona}' MAY approve cross-agency action ` +
      `@persona:${row.persona} @outcome:1 @hazard:bushfire+extreme-heat ` +
      `@fr:FR-007 @clause:II-A @p1`,
    async ({ resolvePersona, page, correlationId }) => {
      const persona = await resolvePersona(row.persona);
      expect(persona.aiims_function).toBe("control");
      await page.setExtraHTTPHeaders({
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      });
      const ws = new WorkspacesPage(page);
      await ws.goto();
      await expect(ws.heading).toBeVisible();
      const incidents = new IncidentsPage(page);
      await incidents.goto();
      await expect(incidents.approveActionButton).toBeVisible();
    },
  );
}

for (const row of NEGATIVE) {
  test(
    `Logistics persona '${row.persona}' MUST NOT approve evacuation ` +
      `@persona:${row.persona} @outcome:2 @hazard:bushfire+severe-storm ` +
      `@fr:FR-007 @clause:II-A @p1`,
    async ({ resolvePersona, page, correlationId }) => {
      const persona = await resolvePersona(row.persona);
      expect(persona.aiims_function).toBe("logistics");
      await page.setExtraHTTPHeaders({
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      });
      const incidents = new IncidentsPage(page);
      await incidents.goto();
      // Logistics personas should NOT see the approve-action affordance.
      await expect(incidents.approveActionButton).toHaveCount(0);
    },
  );
}
