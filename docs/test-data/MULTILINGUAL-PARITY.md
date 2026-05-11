# Spec-039 Multilingual Parity Matrix (FR-070, SC-014, T150)

> Generated audit of `packages/domain/src/domain/seed/alert-templates/` —
> every `template_id` × `locale` combination MUST have a row, with
> `placeholder=true` flagged where the locale row is a placeholder
> rather than a translation.

## MUST locales (FR-070)

`en-AU`, `ar`, `el`, `it`, `vi`, `zh-Hans`

## Accessibility-placeholder locales (A-9, A-10)

`indigenous-placeholder` — Aboriginal & Torres Strait Islander language
slot, requires cultural-authority review per CL-6 / FR-044 before any
real content is supplied.

`auslan-placeholder` — Auslan video alert slot, must remain a placeholder
in the seed catalogue (real video binaries never committed).

## Parity matrix (8 locales × 5 templates = 40 rows)

| template_id            | en-AU | ar  | el  | it  | vi  | zh-Hans | indigenous-placeholder | auslan-placeholder |
|------------------------|:-----:|:---:|:---:|:---:|:---:|:-------:|:----------------------:|:------------------:|
| bushfire-warning       |  ✓    |  ✓  |  ✓  |  ✓  |  ✓  |   ✓     |          ⊘             |         ⊘          |
| flood-evac             |  ✓    |  ✓  |  ✓  |  ✓  |  ✓  |   ✓     |          ⊘             |         ⊘          |
| cyclone-watch          |  ✓    |  ✓  |  ✓  |  ✓  |  ✓  |   ✓     |          ⊘             |         ⊘          |
| earthquake-aftershock  |  ✓    |  ✓  |  ✓  |  ✓  |  ✓  |   ✓     |          ⊘             |         ⊘          |
| heatwave-advisory      |  ✓    |  ✓  |  ✓  |  ✓  |  ✓  |   ✓     |          ⊘             |         ⊘          |

Legend: `✓` = translated row present · `⊘` = placeholder row present
(no real content committed, awaits cultural-authority / accessibility
production sign-off per FR-044, A-9, A-10).

## Verification

CI pin: `tests/integration/test_multilingual_parity.py` reads the seed
files directly and asserts:

1. Every locale file lists exactly the same `template_id` set as `en-AU`.
2. The two `*-placeholder` files exist and every record carries
   `placeholder=true` (or is otherwise marked as a placeholder slot).
3. Every record across every locale carries `wcag_audio_description`
   (placeholder is acceptable per FR-071 / T151).

If a new template is added, all 8 locale files MUST be updated in the
same commit — the parity test fails otherwise.
