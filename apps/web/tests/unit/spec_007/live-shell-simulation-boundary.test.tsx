/**
 * AUD-017 — FR-022: developer environments expose the separate simulation
 * management route without placing simulation data or controls in live views.
 * AUD-018 — the marker CSS must be sticky with a safe z-index.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { AppShell } from "@ama/ui/components/layout/app-shell";

const repoRoot = path.resolve(__dirname, "../../../../..");
const appShellSource = readFileSync(
  path.join(repoRoot, "packages/ui/src/components/layout/app-shell.tsx"),
  "utf8",
);
const globalsCss = readFileSync(
  path.join(repoRoot, "apps/web/src/app/globals.css"),
  "utf8",
);

describe("live app shell simulation boundary", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("keeps the simulation route gated by the developer-environment flag", () => {
    expect(appShellSource).toMatch(/NEXT_PUBLIC_ALLOW_ANONYMOUS_DEV_ACCESS/);
    expect(appShellSource).toMatch(/NODE_ENV\s*===\s*"development"/);
    expect(appShellSource).toMatch(/href:\s*"\/simulations"/);
  });

  it("hides simulation navigation outside developer environments", () => {
    vi.stubEnv("NEXT_PUBLIC_ALLOW_ANONYMOUS_DEV_ACCESS", "0");
    const { container } = render(
      <AppShell>
        <p>live operational content</p>
      </AppShell>,
    );

    const anchors = Array.from(container.querySelectorAll("a"));
    for (const anchor of anchors) {
      expect(anchor.getAttribute("href") ?? "").not.toContain("/simulations");
      expect((anchor.textContent ?? "").toLowerCase()).not.toContain("simulation");
    }
    expect(screen.queryByText(/simulation/i)).toBeNull();
    expect(
      screen.getByRole("button", { name: /toggle navigation/i }),
    ).toBeInTheDocument();
  });

  it("exposes the separate simulation management area in developer environments", () => {
    vi.stubEnv("NEXT_PUBLIC_ALLOW_ANONYMOUS_DEV_ACCESS", "1");
    render(
      <AppShell>
        <p>live operational content</p>
      </AppShell>,
    );

    expect(
      screen.getByRole("link", { name: /simulations/i }),
    ).toHaveAttribute("href", "/simulations");
    expect(screen.queryByText(/simulation dashboard/i)).toBeNull();
  });
});

describe("simulation marker stylesheet", () => {
  const block = globalsCss.slice(
    globalsCss.indexOf(".sim-banner-wrap {"),
    globalsCss.indexOf(".sim-banner-card {"),
  );

  it("pins the marker below the sticky nav", () => {
    expect(block).toMatch(/position:\s*sticky/);
    expect(block).toMatch(/top:\s*60px/);
  });

  it("uses a z-index above overlays but below modal and nav layers", () => {
    expect(block).toMatch(/z-index:\s*calc\(var\(--ama-z-modal, 200\) - 1\)/);
  });

  it("removes the dead local-objectives rules", () => {
    expect(globalsCss).not.toMatch(/^\.sim-objectives \{/m);
    expect(globalsCss).not.toMatch(/^\.sim-obj-add-btn \{/m);
  });
});
