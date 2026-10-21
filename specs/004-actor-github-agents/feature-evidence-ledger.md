# Feature Evidence Ledger: AUD-007, AUD-009, AUD-001, AUD-002, AUD-003, AUD-004, AUD-005, AUD-006, AUD-008, AUD-010, AUD-015, AUD-016, AUD-017

Date: 2026-09-15
Scope: specs/004-actor-github-agents only

## Commands and Results

1. Integrity scanner on touched AUD files:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_content_integrity.py --repo-root . .github/agents/technical/software-developer.agent.md .github/agents/technical/qa-test-engineer.agent.md .github/agents/technical/accessibility-tester.agent.md .github/agents/technical/ai-ml-engineer.agent.md .github/agents/technical/chaos-engineer.agent.md .github/agents/technical/docker-container-engineer.agent.md .github/agents/technical/security-engineer.agent.md .github/agents/technical/ux-designer.agent.md .github/agents/technical/solution-architect.agent.md .github/agents/technical/azure-principal-architect.agent.md .github/agents/technical/infrastructure-devops.agent.md .github/agents/technical/compliance-auditor.agent.md .github/agents/technical/data-engineer.agent.md .github/agents/technical/product-owner-ba.agent.md .github/agents/operational/planning-officer.agent.md .github/agents/operational/public-information-officer.agent.md .github/agents/sectors/commonwealth/bom-national.agent.md
```

Result: PASS (`OK: 17 markdown files passed integrity checks`).

1. Python compile check for new scanner and test:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile tools/lint/check_agent_content_integrity.py tests/unit/test_agent_content_integrity_lint.py
```

Result: PASS (no compile errors).

1. Unit tests for scanner behaviors:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_agent_content_integrity_lint.py
```

Result: PASS (`5 passed in 0.22s`).

1. Static policy tests for AUD-001 and AUD-002:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_actor_aud001_aud002_static.py
```

Result: PASS (`4 passed in 0.13s`).

1. YAML frontmatter parse for all actor files:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "from pathlib import Path; import yaml; files=list(Path('.github/agents').rglob('*.agent.md')); bad=[]
for p in files:
 t=p.read_text(encoding='utf-8')
 if not t.startswith('---\n'):
  bad.append((str(p),'missing frontmatter start')); continue
 try:
  parts=t.split('---',2)
  if len(parts)<3: raise ValueError('frontmatter delimiters not closed')
  yaml.safe_load(parts[1])
 except Exception as e:
  bad.append((str(p),str(e)))
print(f'YAML_FRONTMATTER_OK={len(files)-len(bad)} TOTAL={len(files)}')
[print(f'BAD:{p}:{e}') for p,e in bad]
import sys; sys.exit(1 if bad else 0)"
```

Result: PASS (`YAML_FRONTMATTER_OK=103 TOTAL=103`).

1. Markdown lint (feasibility check):

```powershell
pnpm exec markdownlint .github/agents/operational/planning-officer.agent.md .github/agents/operational/public-information-officer.agent.md .github/agents/sectors/commonwealth/bom-national.agent.md .github/agents/technical/accessibility-tester.agent.md .github/agents/technical/ai-ml-engineer.agent.md .github/agents/technical/azure-principal-architect.agent.md .github/agents/technical/chaos-engineer.agent.md .github/agents/technical/compliance-auditor.agent.md .github/agents/technical/data-engineer.agent.md .github/agents/technical/docker-container-engineer.agent.md .github/agents/technical/infrastructure-devops.agent.md .github/agents/technical/product-owner-ba.agent.md .github/agents/technical/qa-test-engineer.agent.md .github/agents/technical/security-engineer.agent.md .github/agents/technical/software-developer.agent.md .github/agents/technical/solution-architect.agent.md .github/agents/technical/ux-designer.agent.md specs/004-actor-github-agents/contracts/constitutional-grounding.md
```

Result: Not available in environment (`pnpm` not found).

1. Markdown lint fallback:

```powershell
npx --yes markdownlint-cli .github/agents/operational/planning-officer.agent.md .github/agents/operational/public-information-officer.agent.md .github/agents/sectors/commonwealth/bom-national.agent.md .github/agents/technical/accessibility-tester.agent.md .github/agents/technical/ai-ml-engineer.agent.md .github/agents/technical/azure-principal-architect.agent.md .github/agents/technical/chaos-engineer.agent.md .github/agents/technical/compliance-auditor.agent.md .github/agents/technical/data-engineer.agent.md .github/agents/technical/docker-container-engineer.agent.md .github/agents/technical/infrastructure-devops.agent.md .github/agents/technical/product-owner-ba.agent.md .github/agents/technical/qa-test-engineer.agent.md .github/agents/technical/security-engineer.agent.md .github/agents/technical/software-developer.agent.md .github/agents/technical/solution-architect.agent.md .github/agents/technical/ux-designer.agent.md specs/004-actor-github-agents/contracts/constitutional-grounding.md
```

Result: Executed; reported multiple style-level issues across legacy and touched actor markdown files (non-blocking for this scoped AUD implementation).

1. Editor diagnostics check:

Tool: `get_errors` on all touched files plus new scanner and tests.

Result: PASS (no diagnostics errors reported in touched files).

## Notes

- External legal and AFDRS fact verification remains out of scope and unclaimed in this implementation.
- No deploy, no commit, no actor invocation performed.

## AUD-006/AUD-017 Addendum (2026-09-15)

### Commands and Results

1. Canonical AFP file rename to unique IDs:

```powershell
Move-Item .github/agents/sectors/act/afp.agent.md .github/agents/sectors/act/afp-act.agent.md
Move-Item .github/agents/sectors/commonwealth/afp.agent.md .github/agents/sectors/commonwealth/afp-commonwealth.agent.md
```

Result: PASS.

1. Narrow post-first-edit validation (handoff resolution blast-radius check):

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "...frontmatter handoff resolution check..."
```

Result: Expected transitional failures before handoff rewiring (`MISSING 30`, all due to `agent: afp` references pending update).

1. Global active actor uniqueness and handoff exact-resolution verification:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "...active actor uniqueness + handoff exact-resolution check..."
```

Result: PASS (`ACTIVE_FILES 85`, `UNIQUE_IDS 85`, `DUPLICATES 0`, `BAD_HANDOFFS 0`).

1. Full frontmatter parse and handoff resolution across all agent files:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "...all agent files parse + handoff resolution check..."
```

Result: PASS (`ALL_AGENT_FILES 103`, `ALL_UNIQUE_IDS 103`, `ALL_DUPLICATE_IDS 0`, `ALL_HANDOFF_RESOLUTION_ERRORS 0`).

1. Integrity scanner over actor-agent markdown:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_content_integrity.py --repo-root . .github/agents/operational .github/agents/sectors .github/agents/technical
```

Result: PASS (`OK: 91 markdown files passed integrity checks`).

1. Targeted tests including new AUD-006/AUD-017 static assertions:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_actor_aud006_aud017_static.py tests/unit/test_agent_content_integrity_lint.py tests/unit/test_actor_aud001_aud002_static.py
```

Result: PASS (`15 passed in 1.00s`).

### Scope Notes and Residual Blockers

- AUD-006 and AUD-017 were implemented only within `specs/004-actor-github-agents` and directly-related actor/validator files.
- External clean-profile editor discovery verification remains unverified and is intentionally left to AUD-016 scope.

## AUD-003/AUD-015/AUD-016 Addendum (2026-09-15)

### Commands and Results

1. Focused post-first-edit AUD-003 static baseline check:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "...focused active-actor tools policy check..."
```

Result: Baseline captured before remediating actor files (`ACTIVE_ACTORS 85`, `MISSING_TOOLS 82`, `APA_MUTATOR_VIOLATIONS 1`).

1. Bulk active actor tool-policy remediations (explicit tool lists):

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "...update 85 active actor files with explicit tools..."
```

Result: PASS (`CHANGED=85 INSERTED=82 REPLACED=3`).

1. Regenerate actor catalogue from filesystem/frontmatter:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe scripts/generate_agents_catalogue.py --write
```

Result: PASS (`WROTE: .github/agents/AGENTS.md`).

1. Generator idempotency check:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe scripts/generate_agents_catalogue.py --check
```

Result: PASS (`OK: AGENTS.md is up to date`).

1. All-agent frontmatter parse and handoff-resolution check:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "...all .agent.md parse + handoff resolution across non-archived target index..."
```

Result: PASS (`ALL_AGENT_FILES 103`, `PARSE_ERRORS 0`, `HANDOFF_ERRORS 0`).

1. Actor integrity scanner after remediations:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_content_integrity.py --repo-root . .github/agents/operational .github/agents/sectors .github/agents/technical
```

Result: PASS (`OK: 91 markdown files passed integrity checks`).

1. New static tests for AUD-003/AUD-015/AUD-016:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_actor_aud003_aud015_aud016_static.py
```

Result: PASS (`6 passed in 1.32s`).

1. Combined static regression suite:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_actor_aud006_aud017_static.py tests/unit/test_actor_aud003_aud015_aud016_static.py tests/unit/test_agent_content_integrity_lint.py tests/unit/test_actor_aud001_aud002_static.py
```

Result: PASS (`21 passed in 2.04s`).

### Scope Notes and Residual Blockers

- Implemented scope covers AUD-003, AUD-015, and AUD-016 only, in requested order, without deploy/commit/actor invocation.
- Archived actors are now explicitly non-invocable and include successor mappings, and active bodies no longer contain retired generic handoff directives.
- Clean-profile VS Code discovery enumeration evidence remains external to repository static checks and is intentionally left as an external validation activity.

## AUD-008/AUD-005/AUD-004/AUD-010 Addendum (2026-09-15)

### Commands and Results

1. Create and validate authority ledger (narrow check after first edit):

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "...yaml.safe_load('specs/004-actor-github-agents/contracts/authority-ledger.yaml')..."
```

Result: PASS (`OK authority-ledger parse 4`).

1. Regenerate 50 jurisdiction sector actor files + authority ledger:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe scripts/regenerate_sector_agents.py
```

Result: PASS (`Updated 50 jurisdiction sector files and authority ledger`).

1. Sector generator idempotency:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe scripts/regenerate_sector_agents.py
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe scripts/regenerate_sector_agents.py
```

Result: PASS (`SECTOR_IDEMPOTENCY:OK`, ledger hash unchanged on second run).

1. Regenerate AGENTS catalogue and verify no drift:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe scripts/generate_agents_catalogue.py --write
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe scripts/generate_agents_catalogue.py --check
```

Result: PASS (`WROTE .../AGENTS.md`, then `OK: AGENTS.md is up to date`).

1. Full structural validator (all `.agent.md` files, includes 103-frontmatter parse):

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_contract_structure.py --repo-root .
```

Result: PASS (`OK: agent contract structure validation passed`).

1. Integrity scanner:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_content_integrity.py .github/agents --repo-root .
```

Result: PARTIAL (unrelated pre-existing unresolved templated references in non-target files).

1. Scoped integrity scanner for operational/sector/technical actor files:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_content_integrity.py .github/agents/sectors .github/agents/operational .github/agents/technical --repo-root .
```

Result: PASS (`OK: 91 markdown files passed integrity checks`).

1. Structural/semantic regression tests including new AUD suite:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_actor_aud004_aud005_aud008_aud010_static.py tests/unit/test_actor_aud003_aud015_aud016_static.py tests/unit/test_actor_aud006_aud017_static.py tests/unit/test_agent_content_integrity_lint.py
```

Result: PASS (`25 passed in 2.62s`).

### Scope Notes and Residual Blockers

- Implemented scope follows the requested order: AUD-008 -> AUD-005 -> AUD-004 -> AUD-010.
- No deploy, no commit, and no actor invocation were performed.
- External qualified legal/sector verification remains UNVERIFIED in the authority ledger by design; repository assertions stay qualified until primary-source review is attached.

## AUD-011/AUD-012/AUD-013/AUD-014 Addendum (2026-09-15)

### Commands and Results

1. Narrow integrity validation immediately after first edit:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_content_integrity.py --repo-root . .github/agents/operational/observer-auditor.agent.md
```

Result: PASS (`OK: 1 markdown files passed integrity checks`).

1. Full structural validator after scoped remediations:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_contract_structure.py --repo-root .
```

Result: PASS (`OK: agent contract structure validation passed`).

1. Scoped actor integrity scanner:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_content_integrity.py --repo-root . .github/agents/operational .github/agents/sectors .github/agents/technical
```

Result: PASS (`OK: 91 markdown files passed integrity checks`).

1. AUD-011..014 static test suite:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_actor_aud011_aud014_static.py
```

Result: PASS after scoped follow-up fix (`6 passed`).

1. Cross-check with related sector/authority static suite:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_actor_aud011_aud014_static.py tests/unit/test_actor_aud004_aud005_aud008_aud010_static.py
```

Result: PASS (`14 passed in 1.06s`).

1. AGENTS catalogue generator idempotency:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe scripts/generate_agents_catalogue.py --check
```

Result: PASS (`OK: AGENTS.md is up to date`).

1. Full frontmatter parse verification:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "from pathlib import Path; import yaml; files=list(Path('.github/agents').rglob('*.agent.md')); bad=[]
for p in files:
 t=p.read_text(encoding='utf-8')
 if not t.startswith('---\n'):
  bad.append((str(p),'missing frontmatter start')); continue
 try:
  parts=t.split('---',2)
  if len(parts)<3: raise ValueError('frontmatter delimiters not closed')
  yaml.safe_load(parts[1])
 except Exception as e:
  bad.append((str(p),str(e)))
print(f'YAML_FRONTMATTER_OK={len(files)-len(bad)} TOTAL={len(files)}')
[print(f'BAD:{p}:{e}') for p,e in bad]
import sys; sys.exit(1 if bad else 0)"
```

Result: PASS (`YAML_FRONTMATTER_OK=103 TOTAL=103`).

### Scope Notes and Residual Blockers

- Implemented scope is limited to AUD-011, AUD-012, AUD-013, and AUD-014 with checklist override YES.
- No deploy, no commit, and no actor invocation were performed.
- External authority/legal validation remains UNVERIFIED and intentionally qualified in-sector authority wording.

## AUD-018/AUD-019/AUD-020/AUD-021/AUD-022 Addendum (2026-09-15)

### Commands and Results

1. Narrow post-first-edit check on new catalogue validator:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile tools/lint/check_actor_agent_catalogue.py
```

Result: PASS (no compile errors).

1. AUD-018 catalogue validator against checked-in catalogue:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_actor_agent_catalogue.py --root .
```

Result: PASS (`actor-agent-catalogue: PASS`).

1. AUD-019..022 scaffold validator:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_actor_feature_evidence.py --root .
```

Result: PASS (`actor-feature-evidence: PASS`).

1. New unit tests for the new validators:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_actor_agent_catalogue.py tests/unit/test_actor_feature_evidence.py
```

Result: PASS (`15 passed in 0.97s`).

1. Actor integrity scanner:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe tools/lint/check_agent_content_integrity.py --repo-root . .github/agents/operational .github/agents/sectors .github/agents/technical
```

Result: PASS (`OK: 91 markdown files passed integrity checks`).

1. AGENTS generator drift check:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe scripts/generate_agents_catalogue.py --check
```

Result: PASS (`OK: AGENTS.md is up to date`).

1. Full actor frontmatter parse check:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "...yaml.safe_load over .github/agents/**/*.agent.md..."
```

Result: PASS (`YAML_FRONTMATTER_OK=103 TOTAL=103`).

1. CI workflow YAML parse check:

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('.github/workflows/ci.yml').read_text(encoding='utf-8')); print('CI_YAML_PARSE_OK')"
```

Result: PASS (`CI_YAML_PARSE_OK`).

1. Markdownlint for newly created evidence markdown scaffolds:

```powershell
npx --yes markdownlint-cli specs/004-actor-github-agents/evidence/sc-003-operational.md specs/004-actor-github-agents/evidence/sc-004-sectors.md specs/004-actor-github-agents/evidence/sc-005-onboarding.md specs/004-actor-github-agents/evidence/sc-006-timing.md
```

Result: PASS (no lint output).

1. Full actor static suite run (including pre-existing actor static tests):

```powershell
C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q tests/unit/test_actor_aud001_aud002_static.py tests/unit/test_actor_aud003_aud015_aud016_static.py tests/unit/test_actor_aud004_aud005_aud008_aud010_static.py tests/unit/test_actor_aud006_aud017_static.py tests/unit/test_actor_aud011_aud014_static.py tests/unit/test_actor_agent_catalogue.py tests/unit/test_actor_feature_evidence.py tests/unit/test_agent_content_integrity_lint.py
```

Result: PARTIAL (`1 failed, 49 passed`). External blocker remains in `tests/unit/test_actor_aud001_aud002_static.py::test_aud002_required_aws_terms_and_scale_separation` due missing `'Advice'` token in `.github/agents/sectors/commonwealth/bom-national.agent.md`.

### Scope Notes and Residual Blockers

- Implemented scope is limited to AUD-018 through AUD-022 with checklist override YES.
- AUD-018 is complete and enforced by required CI `quality` step (`actor-agent-catalogue-lint`).
- AUD-019 through AUD-022 are marked complete for automatable scaffold/instrument preparation only; external measurements remain open and `Not measured`.
- No deploy, no commit, no actor invocation, and no survey collection were performed.

## Aggregate Validation Correction (2026-09-15)

- Root cause of the earlier AWS test failure: the sector generator omitted the BoM-specific AWS guidance and overwrote the manual correction.
- Root cause of the subsequent DFES/ARC boundary failures: combined-agency and evacuation-centre ownership wording was not represented in the generator's custom-boundary source.
- Corrected `scripts/regenerate_sector_agents.py` so BoM AWS terminology, the DFES combined WA fire/SES boundary, and the ARC/local-government facility/service split survive regeneration.
- Complete feature-004 static suite: PASS (`53 passed in 4.63s`).
- Required gates: `actor-agent-catalogue`, `actor-feature-evidence`, and agent contract structure all PASS.
- Generator state: `AGENTS.md` is up to date; all 91 active actor documents pass integrity checks.
- All 25 remediation tasks are checked for repository-automatable implementation or measurement scaffolding.
- External legal/sector review, clean-profile discovery, actor-answer evaluation, contributor survey, and timed contributor exercise remain explicitly unmeasured/unverified.
