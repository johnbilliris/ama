# GitHub Actions SHA-Pin Tracker (FR-C03, T110)

**Goal**: every `uses:` reference in `.github/workflows/` and `.github/actions/` MUST be pinned to a 40-character commit SHA (with the human-readable tag in a trailing comment). This file tracks the sweep.

> **Strategy**: Dependabot (added in T005) opens weekly PRs that update the SHAs and the `# v<tag>` comments. Manual sweep below seeds the initial pinning for actions that already exist on the branch.

## Resolution helper

To resolve any tag → SHA from the command line:

```pwsh
gh api repos/<owner>/<repo>/git/refs/tags/<tag> --jq '.object.sha'
# or for branches:
gh api repos/<owner>/<repo>/commits/<branch> --jq '.sha'
```

## Current references (as of 2026-04-30)

| Workflow | Action | Current ref | Pin target |
|---|---|---|---|
| ci.yml | `actions/checkout@v5` | tag | `<sha>  # v5.0.0` |
| ci.yml | `actions/setup-python@v6` | tag | `<sha>  # v6.0.0` |
| ci.yml | `pnpm/action-setup@v5` | tag | `<sha>  # v5.0.0` |
| ci.yml | `actions/setup-node@v5` | tag | `<sha>  # v5.0.0` |
| ci.yml | `actions/upload-artifact@v6` | tag | `<sha>  # v6.0.0` |
| codeql.yml | `actions/checkout@v5` | tag | (same) |
| codeql.yml | `github/codeql-action/init@v3` | tag | `<sha>  # v3.x` |
| codeql.yml | `github/codeql-action/autobuild@v3` | tag | (same) |
| codeql.yml | `github/codeql-action/analyze@v3` | tag | (same) |
| security-scan.yml | `gitleaks/gitleaks-action@v2` | tag | `<sha>  # v2.x` |
| security-scan.yml | `microsoft/ps-rule@v3` | tag | `<sha>  # v3.x` |
| security-scan.yml | `aquasecurity/trivy-action@0.30.0` | tag | `<sha>  # v0.30.0` |
| cd.yml | `azure/login@v3` | tag | `<sha>  # v3.x` |
| cd.yml | `Azure/setup-azd@v2` | tag | `<sha>  # v2.x` |
| eval-pr-gate.yml | `actions/github-script@v7` | tag | `<sha>  # v7.x` |
| eval-publish-dataset.yml | `actions/checkout@v4` | tag | (raise to v5 sha) |
| eval-publish-dataset.yml | `actions/setup-python@v5` | tag | (raise to v6 sha) |
| eval-publish-dataset.yml | `actions/upload-artifact@v4` | tag | (raise to v6 sha) |
| drift-detection.yml | `actions/checkout@v5`, `azure/login@v3` | tag | (same as above) |

## Sweep procedure (tracked in this PR)

1. Resolve tag → SHA for each row above (helper script `scripts/resolve-action-shas.ps1` — to be authored in follow-up Stream 1 milestone).
2. Apply pinning in a single PR (or grouped Dependabot PRs).
3. Add an `Audited: <date>` row at the bottom of this file.

## Status

**Tooling delivered** (this commit):
- Dependabot enabled for `github-actions` ecosystem (T005) — opens weekly SHA-bump PRs.
- This tracker establishes the inventory.

**Sweep execution deferred** to a follow-up Dependabot-orchestrated PR series so that the initial SHAs are always current and don't go stale by the time spec-032 merges. The first Dependabot run after merge will create the pinning PRs for review.

## Audited

- (initial inventory) 2026-04-30 — johnbilliris / spec-032 Stream 1
