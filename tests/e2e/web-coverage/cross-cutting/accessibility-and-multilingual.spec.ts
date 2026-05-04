/**
 * T060 — WCAG 2.2 AA + multilingual coverage (FR-014, Q14, Q2).
 *
 * Every P1 surface must pass axe-core's WCAG 2.2 AA tags. Multilingual
 * coverage probed via /api/i18n/coverage.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { buildAxe } from "@web-coverage/_support/a11y/axeBuilder";
import { probeLanguagePack } from "@web-coverage/_support/a11y/languagePackProbe";
import { WorkspacesPage } from "@web-coverage/_support/pages/workspaces.po";
import { GovernanceDashboardPage } from "@web-coverage/_support/pages/governance.dashboard.po";
import { SimulationsPage } from "@web-coverage/_support/pages/simulations.po";

const ROUTES: Array<{ key: string; goto: (page: import("@playwright/test").Page) => Promise<void> }> = [
  { key: "workspaces", goto: async (p) => new WorkspacesPage(p).goto() },
  { key: "governance-dashboard", goto: async (p) => new GovernanceDashboardPage(p).goto() },
  { key: "simulations", goto: async (p) => new SimulationsPage(p).goto() },
];

const REQUIRED_LANGUAGES = ["en", "zh-Hans", "aus-x-atsi-placeholder"];

for (const route of ROUTES) {
  test(
    `WCAG 2.2 AA on ${route.key} ` +
      `@persona:public-information-officer @outcome:1 @hazard:bushfire+extreme-heat ` +
      `@fr:FR-014 @clause:V-C @p1`,
    async ({ resolvePersona, page, correlationId }) => {
      const persona = await resolvePersona("public-information-officer");
      await page.setExtraHTTPHeaders({
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      });
      await route.goto(page);
      const results = await buildAxe(page).analyze();
      expect(
        results.violations,
        results.violations.map((v) => `${v.id}: ${v.help}`).join("\n"),
      ).toEqual([]);
    },
  );
}

test(
  `Language pack covers en+zh-Hans+aus-x-atsi-placeholder ` +
    `@persona:public-information-officer @outcome:1 @hazard:bushfire+extreme-heat ` +
    `@fr:FR-014 @clause:V-C @p1`,
  async ({ request, correlationId }) => {
    const result = await probeLanguagePack(request, REQUIRED_LANGUAGES);
    if (!result.ok) {
      test.info().annotations.push({ type: "gap", description: `language pack missing: ${result.missing.join(", ")}` });
    }
    expect(result.missing, `correlation_id=${correlationId}`).toEqual([]);
  },
);
