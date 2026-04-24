# Template: CODEOWNERS entry for capstone spec

Satisfies FR-034 and Clarification 6. Copy into `.github/CODEOWNERS`. If the file does not yet exist, create it with the line below as the first non-comment entry.

## Fragment

```text
# Capstone specification — dual-control spec maintenance per FR-034.
# Every PR touching this directory requires review from the spec-maintainers team.
specs/001-disaster-response-hub/ @johnbilliris/ama-spec-maintainers
```

## Replacement guidance

- Replace `@johnbilliris/ama-spec-maintainers` with the actual GitHub team handle for this organisation. A **team** handle is mandatory; individual handles are not permitted (Clarification 6 intent: authority survives personnel change).
- The team must have at least **two** members so that a maintainer who drafts a row cannot also be the countersigner.

## Validation rules

1. `.github/CODEOWNERS` contains a non-comment line whose left side is exactly `specs/001-disaster-response-hub/` (trailing slash required for directory scope).
2. The right side is a single team handle (`@org/team-name`); user handles or multiple handles on the same line fail validation.
3. The referenced team exists on GitHub and has ≥ 2 members at the time of verification.

## Extension pattern

When 028 (and future hardening features) ship, add analogous lines, e.g.:

```text
specs/028-holistic-spec-hardening/ @johnbilliris/ama-spec-maintainers
specs/shared/ @johnbilliris/ama-spec-maintainers
```

Each governed directory gets its own CODEOWNERS entry so that the dual-control rule is enforced wherever status-bearing artefacts live.
