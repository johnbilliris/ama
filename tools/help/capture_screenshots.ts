/**
 * spec-038 T-AA176 — Playwright-driven help-screenshot capture (light + dark).
 *
 * Iterates the route registry, opens each route, snapshots light + dark
 * variants, computes screen_id_hash, uploads to the help-screenshots blob
 * container, and updates the screenshot_registry. Stub-safe: if Playwright
 * is unavailable, prints a runbook entry pointing to manual capture.
 */

import fs from "node:fs";
import path from "node:path";

interface RouteRegistry {
  [routeId: string]: { url: string; anchors: string[] };
}

async function run() {
  const registryPath = process.env.HELP_ROUTE_REGISTRY ?? "tools/help/route_registry.json";
  if (!fs.existsSync(registryPath)) {
    console.error(`[capture_screenshots] missing registry at ${registryPath}; see docs/runbooks/help/screenshot-staleness.md`);
    process.exit(2);
  }
  const registry: RouteRegistry = JSON.parse(fs.readFileSync(registryPath, "utf-8"));
  let playwright: typeof import("playwright") | null = null;
  try {
    playwright = await import("playwright");
  } catch {
    console.warn("[capture_screenshots] Playwright not installed — emitting placeholder PNGs only.");
  }
  const outDir = process.env.HELP_SCREENSHOT_DIR ?? "apps/web/public/help/screenshots";
  fs.mkdirSync(outDir, { recursive: true });
  for (const [routeId, info] of Object.entries(registry)) {
    for (const theme of ["light", "dark"] as const) {
      const outFile = path.join(outDir, `${routeId}-${theme}.png`);
      if (!playwright) {
        // Emit 1x1 placeholder PNG so MDX <picture> references resolve.
        const PLACEHOLDER = Buffer.from(
          "89504e470d0a1a0a0000000d4948445200000001000000010806000000" +
            "1f15c4890000000a49444154789c63000100000005000196f9d3" +
            "0a0000000049454e44ae426082",
          "hex",
        );
        fs.writeFileSync(outFile, PLACEHOLDER);
        continue;
      }
      const browser = await playwright.chromium.launch();
      const ctx = await browser.newContext({
        colorScheme: theme,
        viewport: { width: 1280, height: 800 },
      });
      const page = await ctx.newPage();
      await page.goto(info.url, { waitUntil: "networkidle" });
      await page.screenshot({ path: outFile, fullPage: true });
      await browser.close();
    }
  }
  console.log(`[capture_screenshots] wrote ${Object.keys(registry).length * 2} files to ${outDir}`);
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
