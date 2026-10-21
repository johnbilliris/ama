/**
 * AUD-017 — the live Help catalogue must expose no simulation affordance.
 * AUD-018 — the simulation watermark browser test must live under a
 * configured Playwright `testDir` and must fail on absence, not soft-skip.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import HelpPage from "@/app/help/page";

const repoRoot = path.resolve(__dirname, "../../../../..");
const watermarkSpecPath = path.join(
  repoRoot,
  "tests/e2e/web-coverage/cross-cutting/simulation-watermark.spec.ts",
);
const playwrightConfig = readFileSync(
  path.join(repoRoot, "apps/web/playwright.config.cts"),
  "utf8",
);

describe("live help catalogue simulation boundary", () => {
  it("renders no link to a simulation route", () => {
    const { container } = render(<HelpPage />);
    for (const anchor of Array.from(container.querySelectorAll("a"))) {
      expect(anchor.getAttribute("href") ?? "").not.toContain("/simulations");
    }
    expect(screen.queryByRole("link", { name: /simulation/i })).toBeNull();
  });
});

describe("simulation watermark browser test discovery", () => {
  it("lives inside a configured Playwright testDir", () => {
    expect(existsSync(watermarkSpecPath)).toBe(true);
    expect(playwrightConfig).toMatch(/testDir:\s*"\.\.\/\.\.\/tests\/e2e"/);
    expect(playwrightConfig).toMatch(/testDir:\s*"\.\.\/\.\.\/tests\/e2e\/web-coverage"/);
  });

  it("no longer sits outside every testDir", () => {
    expect(
      existsSync(path.join(repoRoot, "apps/web/tests/a11y/simulation-watermark.spec.ts")),
    ).toBe(false);
  });

  it("fails on a missing marker instead of annotating a gap", () => {
    const source = readFileSync(watermarkSpecPath, "utf8");
    expect(source).toMatch(/toBeGreaterThan\(0\)/);
    expect(source).not.toMatch(/annotations\.push/);
    expect(source).not.toMatch(/expect\.soft/);
    expect(source).toMatch(/@a11y/);
  });
});
