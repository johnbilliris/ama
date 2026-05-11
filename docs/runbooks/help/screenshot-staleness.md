# Screenshot Staleness Runbook (FR-010a-AMEND / FR-010b · CHK076)

## Detect
Build-time check `tools/help/check_screenshot_freshness.py` compares
`AnnotatedScreenshot.screen_id_hash` against the live DOM for each
route. Mismatches emit `audit.screenshot_staleness_detected`.

## Bulk re-baseline
1. On a dev box with Playwright browsers installed:
   ```pwsh
   pnpm -C apps/web exec playwright install --with-deps
   pnpm -C apps/web tsx tools/help/capture_screenshots.ts --bulk
   ```
2. Diff PNG + JSON outputs vs the baseline; commit batched updates with
   `screenshot:rebaseline` PR label.
3. Dual content review (UX + accessibility) required for any callout
   number/alt-text change.

## Grace period
- 14 calendar days after a UI change before the build fails on stale
  screenshots.
- During the grace period, the article renders the *prior* screenshot
  with a `[Updated screenshot pending]` badge (component
  `<StaleScreenshotBadge />`).

## Single-screen update
```pwsh
pnpm -C apps/web tsx tools/help/capture_screenshots.ts --route /workspaces/[id]
```

## Audit
Each baseline commit MUST cite the route_id list and the operator id;
`audit.screenshot_rebaselined` is emitted automatically by the script.
