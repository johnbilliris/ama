# Contract: Lint Scripts & CI Job

**Spec refs**: FR-021, FR-022, FR-023, SC-004, SC-008  
**Files**:
- `tools/lint/check_spec_cross_refs.py`
- `tools/lint/check_known_gaps.py`
- `.github/workflows/ci.yml` (new `docs-arch` job)

---

## 1. `check_spec_cross_refs.py`

### Purpose

Assert that every shipped spec number 001–037 (excluding entries in the known-gaps registry marked
as archived or superseded) is cited by at least one file under `docs/architecture/**/*.md`.

### CLI Interface

```
usage: check_spec_cross_refs.py [--root REPO_ROOT]

options:
  --root REPO_ROOT  Repository root directory (default: cwd)

exit codes:
  0   All spec numbers are cited (or excluded via known-gaps)
  1   One or more spec numbers are missing citations
```

### Algorithm

```python
1. Build spec_inventory:
   - List all directories matching specs/[0-9][0-9][0-9]-*/
   - Extract 3-digit prefix; deduplicate (two 036-* dirs → one '036')
   - Result: set of 3-digit strings, e.g. {'001', '010', ..., '037'}

2. Build exclusion_set:
   - Read docs/architecture/known-gaps.md
   - For rows where Area/Spec matches r'^spec-(\d{3})' AND Status == 'Resolved'
     add the 3-digit number to exclusion_set
   - (Archived specs listed as Resolved are excluded from the citation check)

3. required = spec_inventory - exclusion_set

4. Build cited_set:
   - Scan all docs/architecture/**/*.md files
   - Find all occurrences of pattern r'spec[- ]?(\d{3})' (case-insensitive)
   - Collect unique 3-digit numbers

5. missing = required - cited_set

6. If missing:
   - Print sorted list of missing spec numbers with count
   - Exit 1
7. Else:
   - Print "All {n} spec numbers cited."
   - Exit 0
```

### Output on failure

```
FAIL: The following spec numbers are not cited in any docs/architecture/**/*.md page:
  spec-003 (no citation found)
  spec-012 (no citation found)
Total missing: 2

To fix: add a citation (e.g., <!-- spec-cross-ref: spec-003 -->) to at least one
architecture page, or add the spec to docs/architecture/known-gaps.md with a
non-empty Follow-up Task Ref and Status = 'Resolved' if it is archived/superseded.
```

### Dependencies

Standard library only: `pathlib`, `re`, `sys`, `argparse`. Python 3.12.

---

## 2. `check_known_gaps.py`

### Purpose

Assert that every row in `docs/architecture/known-gaps.md` has a non-empty, non-`TBD`
`Follow-up Task Ref`. (Full specification in `contracts/known-gaps-schema.md`.)

### CLI Interface

```
usage: check_known_gaps.py [--root REPO_ROOT]

options:
  --root REPO_ROOT  Repository root directory (default: cwd)

exit codes:
  0   All rows have valid Follow-up Task Refs
  1   One or more rows are invalid
```

### Dependencies

Standard library only: `pathlib`, `re`, `sys`, `argparse`. Python 3.12.

---

## 3. PNG ↔ Draw.io Pairing Check (shell one-liner in CI)

### Purpose

Assert that every `.png` under `docs/architecture/` has a sibling `.drawio`, and every `.drawio`
has a sibling `.png`.

### Commands

```bash
# PNG without .drawio sibling
MISSING=$(find docs/architecture -name '*.png' | while read p; do
  base="${p%.png}"
  [ ! -f "${base}.drawio" ] && echo "$p"
done)
[ -z "$MISSING" ] || { echo "FAIL: PNGs without .drawio sibling:"; echo "$MISSING"; exit 1; }

# .drawio without .png sibling
MISSING=$(find docs/architecture -name '*.drawio' | while read d; do
  base="${d%.drawio}"
  [ ! -f "${base}.png" ] && echo "$d"
done)
[ -z "$MISSING" ] || { echo "FAIL: .drawio files without .png sibling:"; echo "$MISSING"; exit 1; }
```

---

## 4. `docs-arch` CI Job Definition

### Full job specification (to be inserted into `.github/workflows/ci.yml`)

```yaml
  # ---------------------------------------------------------------------------
  # Spec 001 / FR-021, FR-022, FR-023 — Architecture documentation validation.
  # Runs in parallel with the quality job (no needs: dependency).
  # No path filter: spec cross-reference correctness is checked on every PR.
  # ---------------------------------------------------------------------------
  docs-arch:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5.0.0

      - uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.0.0
        with:
          python-version: "3.12"

      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444 # v5.0.0
        with:
          node-version: "24"

      - name: Install lychee (link checker)
        run: |
          LYCHEE_VERSION=v0.15.1
          curl -fsSL "https://github.com/lycheeverse/lychee/releases/download/${LYCHEE_VERSION}/lychee-${LYCHEE_VERSION}-x86_64-unknown-linux-gnu.tar.gz" \
            | tar -xz -C /tmp
          sudo install /tmp/lychee /usr/local/bin/lychee
          lychee --version

      # FR-022: Markdown lint
      - name: markdownlint
        run: npx --yes markdownlint-cli2 "docs/architecture/**/*.md"

      # FR-021b: Internal link check (scoped to docs/architecture/)
      - name: link-check
        run: |
          lychee \
            --base docs/architecture \
            --include 'docs/architecture' \
            --max-retries 2 \
            --timeout 30 \
            --no-progress \
            "docs/architecture/**/*.md"

      # FR-021a: PNG ↔ .drawio pairing
      - name: png-drawio-pairing
        run: |
          FAIL=0

          # Every .png must have a sibling .drawio
          while IFS= read -r png; do
            base="${png%.png}"
            if [ ! -f "${base}.drawio" ]; then
              echo "FAIL: PNG without .drawio sibling: $png"
              FAIL=1
            fi
          done < <(find docs/architecture -name '*.png')

          # Every .drawio must have a sibling .png
          while IFS= read -r drawio; do
            base="${drawio%.drawio}"
            if [ ! -f "${base}.png" ]; then
              echo "FAIL: .drawio without .png sibling: $drawio"
              FAIL=1
            fi
          done < <(find docs/architecture -name '*.drawio')

          [ "$FAIL" -eq 0 ] || exit 1
          echo "PNG ↔ .drawio pairing: OK"

      # FR-021d: SHA256 hash manifest check
      - name: hash-manifest-check
        working-directory: docs/architecture
        run: |
          sha256sum --check .diagram-hashes
          echo "Hash manifest: all $(wc -l < .diagram-hashes) entries matched."

      # FR-021c, FR-011: Spec cross-reference coverage (001–037)
      - name: spec-cross-ref-check
        run: python tools/lint/check_spec_cross_refs.py

      # FR-023, SC-008: Known-gaps registry completeness
      - name: known-gaps-check
        run: python tools/lint/check_known_gaps.py
```

### Trigger behaviour

| Trigger | Runs? | Notes |
|---------|-------|-------|
| Push to `main` | ✅ | |
| Push to `dev` | ✅ | |
| Push to `staging` | ✅ | |
| Push to `production` | ✅ | |
| PR to `main` | ✅ | |
| Push to feature branch (not PRed) | ❌ | Standard GitHub Actions PR trigger behaviour |

### Path filter

None — runs on every PR regardless of which files changed (spec assumption Q5: ensures spec
cross-reference correctness is checked even when no architecture files are modified).

### Parallelism

`docs-arch` has **no `needs:` dependency** on the `quality` job. Both run in parallel. This avoids
adding latency to the critical path.

---

## Contract Invariants

| # | Invariant | Enforced by |
|---|-----------|-------------|
| 1 | `docs-arch` job must not have `needs: [quality]` | Code review |
| 2 | `docs-arch` job runs on same triggers as `quality` | ci.yml definition |
| 3 | `check_spec_cross_refs.py` must use stdlib only | Code review + import-linter |
| 4 | `check_known_gaps.py` must use stdlib only | Code review + import-linter |
| 5 | `lychee` install step pins a version tag | ci.yml definition |
| 6 | `npx markdownlint-cli2` uses `--yes` to suppress interactive prompts | ci.yml definition |
| 7 | hash-manifest-check runs from `docs/architecture/` working directory | ci.yml `working-directory` |
