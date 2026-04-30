# Contributing to AMA — Autonomous Disaster Response Coordination Hub

Thank you for considering a contribution. This document covers branch conventions, the spec-driven workflow, and the local quality gates that mirror CI.

## TL;DR

1. Pick (or open) a `specs/<NNN>-<short-name>/` feature spec.
2. Branch from the matching environment branch (`dev` for new work; `staging`/`production` only for hot-fixes).
3. Run `pre-commit install`; let the hooks gate every commit.
4. Open a PR into `main` (for shared work) or directly into `dev` (for environment-targeted work).
5. CI gates: ruff, mypy --strict, import-linter, ruff-format, pytest (--cov), CodeQL, web build, benchmarks, web e2e (where applicable).

## Branch model

The repo follows the simplified branch-equals-environment model from spec 031:

| Branch | Purpose | Auto-deploys to |
|---|---|---|
| `main` | Default integration branch; PR target for shared work | (no env) |
| `dev` | Active development environment | `dev` (Container Apps + App Service in `rg-drh-dev`) |
| `staging` | Pre-prod | `staging` |
| `production` | Production | `production` |

Feature branches use the spec name: `NNN-short-name` (e.g. `032-rubric-improvements`). They land in `main` first via PR; once `main` is merged into an environment branch, CI runs and CD deploys.

## Spec-driven workflow

Every non-trivial change starts with a spec:

1. `/speckit.specify` — write `spec.md` from a feature description.
2. `/speckit.clarify` (optional, ≤ 2 passes) — resolve ambiguities.
3. `/speckit.checklist` — generate a requirements-quality checklist.
4. `/speckit.plan` — produce `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`.
5. `/speckit.tasks` — produce `tasks.md` (dependency-ordered).
6. `/speckit.analyze` — cross-artefact consistency check.
7. `/speckit.implement` — execute tasks in order, with frequent commits.

Step 7 is iterative; each milestone passes through `pre-commit` + the canonical CI command before merging.

## Local quality gates (mirror CI)

```pwsh
pip install -e ".[dev]"
pnpm -w install
pre-commit install
pre-commit run --all-files       # ruff, mypy, import-linter, gitleaks, bicep-lint
ruff check apps tests packages
ruff format --check apps tests packages
mypy --strict apps packages
python -m pytest tests/unit tests/integration tests/contract -q --tb=line --cov
```

If any gate fails, fix it locally rather than rely on CI.

## Code conventions

- **Python 3.12+**, Pydantic v2 models, type hints required (`mypy --strict`).
- **TypeScript 5.8+**, strict mode in `tsconfig.json`.
- **Bicep** templates follow the AVM-first policy in `.github/instructions/bicep-code-best-practices.instructions.md`.
- **Imports** must respect the boundaries in `pyproject.toml` `[tool.importlinter]` (e.g. `apps.agents` MUST NOT import from `apps.api`).
- **Comments** only where the code isn't self-explanatory; see `.github/instructions/code-commenting.instructions.md`.

## Commit & PR conventions

- Use conventional-style imperative subject lines: `feat(...)`, `fix(...)`, `docs(...)`, `chore(...)`.
- Every commit MUST include the trailer:
  `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` when assisted by Copilot CLI.
- PRs against `main` need at least one reviewer approval (per Constitution `Governance`).
- Infrastructure changes need a What-If/Plan diff in the PR body.
- Public-facing outputs (warnings, maps, dashboards) need a human-operator review note.

## Reporting issues

- Bug report → open a GitHub issue with the `bug` label.
- Security finding → email security via the address in `SECURITY.md` (do **not** open a public issue).
- Spec gap → open an issue with the `spec` label and reference the affected `specs/<NNN>-...` folder.

## Constitution

The non-negotiable principles live in `.specify/memory/constitution.md`. Every contribution that touches life-safety paths, data residency, or the audit chain must explicitly justify how it preserves those principles in the PR body.
