// Build the deployable bundle for App Service.
//
// Background
// ----------
// Next.js's `output: "standalone"` produces a tiny tree at
// `.next/standalone/`, but inside a pnpm workspace that tree is a forest of
// symlinks pointing at absolute Windows paths under
// `<workspace>/node_modules/.pnpm/...`. Those Windows-absolute targets do
// not survive zip-deploy to a Linux App Service and crash the process at
// `require('next')` with `MODULE_NOT_FOUND`.
//
// Strategy
// --------
// We don't ship the standalone bundle. Instead we use `pnpm deploy` (with
// `--node-linker=hoisted`) to materialise a *flat*, symlink-free
// `node_modules/` tree alongside a copy of the project's source. Then we
// strip dev/test artifacts so the upload stays under ~500 MB. App Service
// runs `next start` directly out of the deploy root.
//
// The standalone build itself is harmless if it still runs — Next.js emits
// it whenever `output: "standalone"` is set in `next.config.ts` — we just
// don't deploy from it.
import { execSync } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(here, "..");
const workspaceRoot = resolve(webRoot, "..", "..");
const deployDir = resolve(webRoot, ".next", "standalone-deploy");

// 1. Wipe any prior deploy bundle.
if (existsSync(deployDir)) {
  rmSync(deployDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}

// 2. Run `pnpm deploy` with hoisted node_modules to produce a flat,
//    symlink-free dependency tree.
console.log(`[copy-standalone-assets] running pnpm deploy → ${deployDir}`);
execSync(
  `pnpm --filter @ama/web --prod --legacy --config.node-linker=hoisted deploy "${deployDir}"`,
  { cwd: workspaceRoot, stdio: "inherit" },
);

// 3. Remove dev/test artifacts and Next.js build caches that pnpm copied
//    along with the project source. These do not affect runtime.
const prunePaths = [
  // .next subdirs unused at runtime
  resolve(deployDir, ".next", "dev"),
  resolve(deployDir, ".next", "cache"),
  resolve(deployDir, ".next", "standalone"),
  resolve(deployDir, ".next", "trace"),
  resolve(deployDir, ".next", "trace-build"),
  resolve(deployDir, ".next", "smoke.out"),
  resolve(deployDir, ".next", "smoke.err"),
  resolve(deployDir, ".next", "diagnostics"),
  // test sources / fixtures
  resolve(deployDir, "__tests__"),
  resolve(deployDir, "tests"),
  resolve(deployDir, "e2e"),
  resolve(deployDir, "test-results"),
  resolve(deployDir, "scripts"),
  // dev configs not needed at runtime
  resolve(deployDir, "playwright.config.cts"),
  resolve(deployDir, "vitest.config.ts"),
  resolve(deployDir, "eslint.config.mjs"),
  resolve(deployDir, "tsconfig.tsbuildinfo"),
  resolve(deployDir, "Dockerfile"),
  resolve(deployDir, ".env.local"),
];
for (const p of prunePaths) {
  if (existsSync(p)) {
    rmSync(p, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
  }
}

console.log(`[copy-standalone-assets] deploy bundle ready at ${deployDir}`);
