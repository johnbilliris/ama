# Contract: Known-Gaps Registry Schema

**File**: `docs/architecture/known-gaps.md`  
**Consumed by**: `check_known_gaps.py` lint script; `docs-arch` CI job; human reviewers  
**Spec refs**: FR-023, SC-008, spec clarification Q4

---

## Purpose

The `known-gaps.md` registry is the canonical list of architecture areas or spec numbers not yet
fully documented, deferred diagrams, and migration tasks. Every row is a tracked gap with a
mandatory follow-up reference. The CI job fails if any row has an empty or placeholder
`Follow-up Task Ref`, preventing undocumented technical debt from reaching `main`.

---

## File Location

```
docs/architecture/known-gaps.md
```

---

## Table Schema

The registry must contain a single Markdown table with **exactly** these column headers, in this
order:

```markdown
| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
```

### Column definitions

| Column | Type | Required | Validation |
|--------|------|----------|------------|
| `Area/Spec` | string | ✅ | Gap identifier (e.g., `BICEP-DEP-01`, `spec-037`); unique per row |
| `Gap Description` | string | ✅ | One sentence describing what is missing or deferred |
| `Follow-up Task Ref` | string | ✅ | **Must not be empty or `TBD`** — use GitHub issue number, PR number, `tasks.md` anchor, or other resolvable reference |
| `Date Identified` | `YYYY-MM-DD` | ✅ | ISO 8601 date when gap was recorded |
| `Status` | enum | ✅ | One of: `Open`, `In Progress`, `Resolved` |

---

## Example Valid Row

```markdown
| BICEP-DEP-01 | Bicep module dependency graph deferred; requires auto-generation from `infra/bicep/` | tasks.md#bicep-dep-graph | 2026-05-11 | Open |
```

## Example Invalid Row (will fail CI)

```markdown
| spec-037 | No architecture page covers spec-037 | TBD | 2026-05-11 | Open |
```

```
ERROR: known-gaps row 'spec-037' has empty or placeholder Follow-up Task Ref ('TBD').
Every row must carry a resolvable task reference. See specs/001-arch-docs-refresh/contracts/known-gaps-schema.md.
```

---

## Page Structure

The `docs/architecture/known-gaps.md` page follows this structure:

```markdown
# Architecture Known Gaps

> Maintained as part of spec-001 (FR-023). CI fails if any row has an empty Follow-up Task Ref.
> See [quickstart.md](../../../specs/001-arch-docs-refresh/quickstart.md) for how to add an entry.

## Open Gaps

| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
|-----------|----------------|-------------------|----------------|--------|
| BICEP-DEP-01 | ... | tasks.md#bicep-dep-graph | 2026-05-11 | Open |
...

## Resolved Gaps

| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
|-----------|----------------|-------------------|----------------|--------|
(rows moved here when Status = Resolved)
```

Multiple tables are permitted (e.g., one per status group). The CI parser checks **all** tables in
the file.

---

## `check_known_gaps.py` Parsing Logic

```
1. Read docs/architecture/known-gaps.md
2. Find all Markdown table rows (lines matching `| ... |`)
3. Skip header rows (containing 'Area/Spec' or '---|')
4. For each data row:
   a. Split on '|'; strip whitespace
   b. Extract column[2] (Follow-up Task Ref, 0-indexed from first non-empty cell)
   c. Assert: column[2] is not empty string and not equal to 'TBD' (case-insensitive)
5. Report all failing rows with row number and value
6. Exit 1 if any failures; exit 0 if clean
```

**Arguments**:

```
usage: check_known_gaps.py [--root REPO_ROOT]

optional arguments:
  --root REPO_ROOT  Repository root (default: current working directory)
```

**Output on failure**:

```
FAIL: docs/architecture/known-gaps.md row 5: Follow-up Task Ref is empty or 'TBD'
  Row content: | spec-037 | No page covers spec-037 | TBD | 2026-05-11 | Open |
Total failures: 1
```

---

## Invariants

1. The file must exist at `docs/architecture/known-gaps.md`.
2. Every table row must have a non-empty, non-`TBD` `Follow-up Task Ref`.
3. The `Area/Spec` identifier should be unique within the file (warning, not error).
4. `Resolved` rows should not be deleted — move them to the `## Resolved Gaps` section to
   preserve audit trail.
