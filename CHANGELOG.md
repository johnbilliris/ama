# Changelog

All notable changes to this repo are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/) once a `1.0.0` tag is cut.

## [Unreleased]

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
