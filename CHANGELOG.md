# Changelog

All notable changes to this repo are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/) once a `1.0.0` tag is cut.

## [Unreleased]

### Added (spec 035 — Webapp capstone closure)
- 9 operator panels (FR-001..FR-008): IC approval card (T036), AWS warning composer (T037), audit timeline (T038), risk matrix (T039), planning IAP (T042), span-of-control warning (T043), field-coordinator offline (T041), resilience handover-PDF (T044), classifier-mask banner (T046).
- 13 sector workspaces under `apps/web/src/app/(operations)/sectors/` covering FR-014..FR-024 / FR-029 across SAPOL, SES SA, DFES WA (cultural-safety + iron-ore-haul), AT TAS island isolation, TasPol multilingual, AFP ACT precinct, SES ACT, NTES multilingual, SJA NT tropical, BoM broadcast, NEMA DACC JATWC, and the utility/insurance recovery sector.
- Cultural-safety subsystem (T053, FR-016, NN-4): elder-routing + 90-second-timeout decision service with closed-set outcomes `cultural_safety_timeout_override` / `cultural_safety_held` and AWS-level allowlist for IC overrides.
- Language pack registry (T050, NN-4 v1 baseline): Simplified Chinese + 5 ATSI community packs with reviewer-required fallback chain, wired into the PIO composer (T073).
- Recovery dashboard extension (T063..T065, FR-024 + SC-005): claims-velocity dashboard, FR-024 built/economic recovery environments, Sendai counterfactual ratio + threshold warning, claims-velocity dollars-paid / dollars-lodged timeline.
- US-3 reusable subsystems (T050..T052): cultural-safety panel, infrastructure overlay (iron-ore haul road, port critical, island logistics, federal precinct), claims-velocity dashboard.
- Cross-cutting horizontals (US-5): SovereigntyBanner with carve-out badge (T069), Foundry carve-out registry (T070, FR-029) + 90-day CI review gate (T071, `.github/workflows/foundry-carveout-review.yml`), generalised offline subsystem registration via `(operations)/layout.tsx` (T072), multilingual fallback chain wiring (T073).
- Audit observability (T078): `ama.audit.outcome` OTEL span attribute helper in `apps/api/app/observability/audit_span.py`, emitted by the cultural-safety service so every closed-set outcome is searchable in Application Insights.
- Architecture diagrams (T079): middleware stack + offline-replay flow in `docs/architecture/spec-035-middleware-and-offline.md`.

### Added (spec 032 — Rubric Improvements, in progress)
- 9-step speckit orchestration artefacts under `specs/032-rubric-improvements/` (spec, plan, research, data-model, quickstart, contracts, two checklists, tasks, analysis).
- `.pre-commit-config.yaml` with ruff/mypy/import-linter/gitleaks/bicep-lint hooks (FR-Q04, T001).
- `tests/README.md` describing each test tier (FR-T06, T002).
- `CONTRIBUTING.md` covering branch model + spec-driven workflow (FR-DOC04, T003).
- `CHANGELOG.md` (this file) (FR-DOC05, T004).
- `.github/dependabot.yml` weekly updates for Dockerfiles + GitHub Actions (FR-D02, T005).

### Changed
- README agent table to include `dependency-notifier` as a first-class agent (FR-AG04, T010).

## [Earlier history]

See `git log` and `specs/*/spec.md` for prior feature deliveries (specs 001–031).
