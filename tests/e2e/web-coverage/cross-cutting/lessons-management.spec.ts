/**
 * T068 — Lessons management → preparedness loop (US4 #3, FR-006 PPRR).
 *
 * /simulations/reports/[reportId] export includes lessons identified;
 * those lessons map to preparedness controls in /preparedness.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { PreparednessPage } from "@web-coverage/_support/pages/preparedness.po";

test(
  `Lessons identified from simulation map to preparedness controls ` +
    `@persona:resilience-planner @outcome:5 @hazard:flood+economic ` +
    `@fr:FR-006 @clause:VII @p1`,
  async ({ resolvePersona, page, request, correlationId }) => {
    const persona = await resolvePersona("resilience-planner");
    await page.setExtraHTTPHeaders({
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    });

    const reportRes = await request.get("/api/simulations/reports/latest", {
      headers: { "X-Correlation-Id": correlationId, "X-Test-Persona-Id": persona.persona_id },
    });
    if (!reportRes.ok()) {
      test.fail(true, "Simulation reports API not wired (FR-006 gap)");
      return;
    }
    const report = (await reportRes.json()) as { lessons?: Array<{ id: string }> };
    const lessonIds = (report.lessons ?? []).map((l) => l.id);
    expect(lessonIds.length).toBeGreaterThan(0);

    const prep = new PreparednessPage(page);
    await prep.goto();
    for (const id of lessonIds) {
      await expect(page.getByTestId(`preparedness-control-${id}`)).toBeVisible();
    }
  },
);
