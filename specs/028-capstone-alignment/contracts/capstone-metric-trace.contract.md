# Contract: `specs/shared/capstone-metric-trace.md`

**Feature**: `028-capstone-alignment`
**Consumers**: rubric evaluators; PR reviewers; automated SC-002 / SC-007 checks.
**Producers**: authors of this feature (028) and any future feature promoting a row from `Deferred` to `Validated`.

## Structure

- The file is exactly one H1, one short intro paragraph, and one Markdown table. No other content.
- The table has the following columns in this order:

  | Column | Type | Required | Notes |
  | --- | --- | --- | --- |
  | Metric | enum | yes | One of `LIVES_SAVED`, `RESPONSE_SPEED`, `EVAC_LEAD_TIME`, `LOGISTICS_EFFICIENCY`, `ECONOMIC_LOSS_REDUCTION`. |
  | Country Cohort | enum | yes | One of `AU-v1`, `PH`, `JP`, `BD`. |
  | SC Owner | string | yes | Format `<spec>:<SC-id>` (e.g., `001:SC-004`) or literal `Deferred — preconditions: <text>`. |
  | HYP Owner | string | yes | Format `<spec>:<HYP-id>` or literal `Deferred — preconditions: <text>`. |
  | Baseline | string | yes | Quantitative baseline with units. |
  | Measurement Method | string | yes | How the value is measured (cite data source or evaluation method). |
  | Status | enum | yes | One of `Validated`, `Deferred`, `Unresolved`. |

## Cardinality

- Exactly 5 × 4 = **20 rows**. No more, no fewer.
- Primary key: `(Metric, Country Cohort)`. No duplicate pairs.

## Validation rules

1. Row count = 20.
2. Every `(Metric, Country Cohort)` pair from the cross-product appears exactly once.
3. `Status = Unresolved` MUST NOT remain when this feature closes (FR-013, SC-002).
4. `Status = Deferred` requires both `SC Owner` and `HYP Owner` cells to begin `Deferred — preconditions: ` with a non-empty precondition list.
5. `Status = Validated` requires both owner cells to match `^[0-9]{3}:(SC|HYP)-[0-9]{3}$` and the referenced ID to exist in the cited spec.

## Example (illustrative only)

```markdown
# Capstone Metric Trace

Maps every capstone success metric to its SC and HYP owner per country cohort. Primary key: (Metric, Country Cohort). Status ∈ {Validated, Deferred, Unresolved}.

| Metric | Country Cohort | SC Owner | HYP Owner | Baseline | Measurement Method | Status |
| --- | --- | --- | --- | --- | --- | --- |
| RESPONSE_SPEED | AU-v1 | 001:SC-004 | 001:HYP-001 | 58 min (AEMS 2023) | AEMS national dataset | Validated |
| RESPONSE_SPEED | PH | Deferred — preconditions: NDRRMC partnership + PAGASA feed | Deferred — preconditions: PH agent deployment | n/a | n/a | Deferred |
```

## Change control

- Append/modify only via a spec-numbered feature.
- Rows progress `Unresolved` → `Deferred` → `Validated` unidirectionally; regressions require documented rationale in the owning spec's clarifications.
