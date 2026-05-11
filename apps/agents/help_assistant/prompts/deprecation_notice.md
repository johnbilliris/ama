# spec-038 — Deprecation-notice template (FR-011d / FR-011d-AMEND).

When a deep link resolves to superseded content, prepend the answer with
this notice (or, when no replacement exists, emit only the notice and a
refusal of kind ``deprecated_no_replacement``).

## current_replacement variant

> **Updated page:** The page at ``{old_slug}`` has been superseded by
> ``{replacement_slug}`` in snapshot ``{snapshot_id}``. The answer below comes
> from the current version.

## withdrawn_no_replacement variant

> **Page withdrawn:** ``{old_slug}`` was withdrawn from the help corpus in
> snapshot ``{snapshot_id}`` with no replacement. Please contact your
> support handoff destination ({support_handoff_label}).
