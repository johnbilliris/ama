# Web Coverage Test Suite (spec 034)

> Playwright-driven capstone coverage tribunal for AMA. Proves the 5 capstone
> outcomes are exercised across all 68 personas, emits a deterministic trace
> + gap register, and gates merges to `main`.

## Layout

```
tests/e2e/web-coverage/
├── _support/              # fixtures, page objects, validators, types, reporter
│   ├── webCoverageTest.ts # merged test surface (persona + scenario + correlation + audit)
│   ├── fixtures/          # 4 baseTest.extend(...) modules + 5 outcome JSON fixtures
│   ├── pages/             # 9 page objects
│   ├── validators/        # outcome-proxy, aws-cap, pspf
│   ├── a11y/              # axeBuilder, languagePackProbe
│   ├── reporter/          # custom Playwright reporter -> coverage-trace.partial-N.json
│   └── types/             # TypeScript contracts (CoverageTraceRow, GapRegisterEntry, …)
├── cross-cutting/         # 15 specs covering rbac/cop/audit/aws/evac/recovery/…
├── operational/           # 10 specs (T069–T078) — the AIIMS function leads
├── sectors/
│   ├── nsw/   vic/   qld/   sa/   wa/   tas/   act/   nt/    # state/territory specs
│   ├── commonwealth/                                          # Cwlth bridge specs
│   ├── cross-sector/                                          # NGO + utilities + ADF
│   └── …                                                      # 9 *.cross-jurisdiction.* specs
├── capstone/              # 5 SC-001..SC-005 outcome closure specs (T146–T150)
└── README.md              # ← you are here
```

Generator: `scripts/web-coverage/_lib/persona_spec_generator.py` is the
**single source of truth** for the 77 persona specs. Edit the inline `Spec`
list there, re-run `python scripts/web-coverage/_lib/persona_spec_generator.py`,
and commit the regenerated `.spec.ts` files alongside the change.

## Tag taxonomy (R-017)

Every persona / capstone spec MUST emit the following tags via the test
title so the custom reporter can derive coverage trace rows:

| Tag           | Form                            | Notes                                                                  |
| ------------- | ------------------------------- | ---------------------------------------------------------------------- |
| `@persona:`   | `@persona:incident-commander`   | Must match a `persona_id` in `identities_australia.json`.              |
| `@outcome:`   | `@outcome:1` … `@outcome:5`     | One of the 5 capstone outcomes (FR-018).                               |
| `@hazard:`    | `@hazard:bushfire+severe-storm` | Lower-kebab; concurrent hazards joined with `+` (FR-026).              |
| `@fr:`        | `@fr:FR-008` (multi allowed)    | Must reference an FR in spec.md.                                       |
| `@clause:`    | `@clause:I` `@clause:NN-1`      | Must reference a Constitution clause; multi allowed.                   |
| `@p1`         | _bareword_                      | The CI smoke filter (`--grep "@p1"`) selects these for fast feedback.  |

Specs that intentionally fail because an API surface is not yet wired use
`test.fail(true, "<reason>")` so the reporter still emits a row and the
gap-register CLI can capture the GAP automatically.

## Persona-id → spec map (68 personas)

The 10 operational personas are exercised once each in `operational/`:

| File                                                                   | Persona id            |
| ---------------------------------------------------------------------- | --------------------- |
| `incident-commander.bushfire-extreme-heat.spec.ts`                     | `incident-commander`  |
| `executive-leader.economic-environment-view.spec.ts`                   | `executive-leader`    |
| `operations-officer.bushfire-severe-storm.spec.ts`                     | `operations-officer`  |
| `planning-officer.tropical-cyclone-flood.spec.ts`                      | `planning-officer`    |
| `logistics-officer.bushfire-cyclone-logistics.spec.ts`                 | `logistics-officer`   |
| `public-information-officer.flood-storm-economic.spec.ts`              | `public-information-officer` |
| `field-coordinator.offline-gps-hazard-report.spec.ts`                  | `field-coordinator`   |
| `resilience-planner.recovery-environments.spec.ts`                     | `resilience-planner`  |
| `risk-manager.span-of-control-tier-2.spec.ts`                          | `risk-manager`        |
| `observer-auditor.audit-trail-readonly.spec.ts`                        | `observer-auditor`    |

The 58 sector personas are exercised across `sectors/{nsw|vic|qld|sa|wa|tas|act|nt|commonwealth|cross-sector}/`. The 9 cross-jurisdiction handover specs (`*.cross-jurisdiction.*`) double up — naming a primary + secondary persona — to satisfy FR-018's ≥ 8 cross-jurisdiction requirement.

To regenerate the map:

```pwsh
python scripts/web-coverage/_lib/persona_spec_generator.py
```

## Hazard-pair fixture index

The five outcome fixtures under `_support/fixtures/data/` define each
outcome's canonical hazard pair:

| Fixture                                          | Outcome | Hazard                            | SC      |
| ------------------------------------------------ | ------: | --------------------------------- | ------- |
| `outcome-1-bushfire-extreme-heat.fixture.json`   | 1       | `bushfire+extreme-heat`           | SC-001  |
| `outcome-2-bushfire-severe-storm.fixture.json`   | 2       | `bushfire+severe-storm`           | SC-002  |
| `outcome-3-tropical-cyclone-flood.fixture.json`  | 3       | `tropical-cyclone+riverine-flood` | SC-003  |
| `outcome-4-bushfire-cyclone-logistics.fixture.json` | 4    | `bushfire+tropical-cyclone`       | SC-004  |
| `outcome-5-flood-storm-economic.fixture.json`    | 5       | `riverine-flood+severe-storm`     | SC-005  |

Specs that need a different hazard for persona-coverage purposes (e.g.,
WA-cyclone, NT-bushfires) ship their own scenario seed via
`POST /api/test-support/seed/scenario`.

## ESLint determinism rules

`eslint.config.*` ships a custom rule that bans `page.waitForTimeout()` in
this directory tree (FR-006 determinism). Use `expect.poll()` or web-first
locator assertions instead.

## Local run snippets

| Goal                              | Command                                                                                              |
| --------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `@p1` smoke (≈ 90s)               | `pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium --grep "@p1"`           |
| Full Chromium suite               | `pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium`                        |
| Mobile / axe-only sweeps          | `pnpm --filter @ama/web test:web-coverage:mobile` / `:axe`                                           |
| Determinism check (3× back-to-back) | `pwsh scripts/web-coverage/verify-trace-determinism.ps1`                                           |
| Merge shards into canonical trace | `python scripts/web-coverage/trace-merge.py --inputs … --out-md … --out-json …`                      |
| Open / promote / close a gap      | `python scripts/web-coverage/gap-register.py {open\|promote\|close\|regress\|escalate} …`            |
| Refresh known-good after deploy   | `python scripts/web-coverage/known-good.py update --commit … --revisions-json … --trace …`           |

See `specs/034-webapp-capstone-coverage/quickstart.md` for the full ≤ 30 min
cold-start walkthrough.
