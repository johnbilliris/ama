# Checklist: MANIFEST.md Freshness Gate (Amendment Cycle 1)

**Purpose**: Unit-test the *requirements quality* of the amendment that introduced FR-036, SC-016, the refinements to FR-031, and the new edge case "Manifest renderer skipped or forgotten" (clarifications CL-9 / CL-10 / CL-11 / CL-12).
**Scope**: AMENDMENT ONLY — does not re-validate the original 281-item baseline (existing 6 checklists remain authoritative for original scope).
**Created**: 2026-05-11
**Feature**: `specs/038-test-data-provisioning/`
**Mode**: Binary (yes/no) — every item is a single closed question against the spec text as written.

---

## Renderer Determinism Contract

- [X] CHK001 - Is the renderer's sort key (`(category, id)`) explicitly named in the spec as part of the locked deterministic contract? [Clarity, Spec §FR-036]
- [X] CHK002 - Is the line-ending terminator (LF) explicitly named as part of the renderer's locked contract? [Clarity, Spec §FR-036]
- [X] CHK003 - Is the encoding (UTF-8) explicitly named as part of the renderer's locked contract? [Clarity, Spec §FR-036]
- [X] CHK004 - Does the spec require that any change to the renderer's deterministic contract be accompanied by an update to FR-036 (preventing silent drift)? [Completeness, Spec §FR-036]

## Lint Exit-Code Semantics

- [X] CHK005 - Is the success exit code (`0`) explicitly specified for the freshness lint? [Clarity, Spec §SC-016]
- [X] CHK006 - Is the divergence exit behaviour (non-zero) explicitly specified? [Clarity, Spec §FR-036, §SC-016]
- [X] CHK007 - Is the N/A skip behaviour specified to also exit `0` (not non-zero, not "no output") on branches lacking `manifest.json`? [Clarity, Spec §SC-016, CL-10]

## CI Wiring (Single Step in Existing `quality:` Job)

- [X] CHK008 - Does the spec require the lint to run as a step inside the EXISTING `quality:` job in `.github/workflows/ci.yml`? [Clarity, Spec §FR-036, CL-9]
- [X] CHK009 - Does the spec explicitly forbid introducing a new GitHub workflow file for this gate? [Completeness, Spec §FR-036, CL-9]

## Failure-Message Contract

- [X] CHK010 - Does the spec require the lint to print a unified diff of the two normalised buffers on failure? [Completeness, Spec §FR-036, CL-10]
- [X] CHK011 - Does the spec require the lint to print the EXACT remediation command (`python tools/lint/build_test_data_manifest.py && python tools/lint/render_test_data_manifest_md.py`) on failure? [Clarity, Spec §FR-036, §SC-016, CL-10]
- [X] CHK012 - Does the spec acknowledge a "sensible line budget" / truncation requirement for the diff so CI logs remain readable? [Completeness, Spec §FR-036, CL-10]

## Comparison Method (Byte-Exact + Normalisation)

- [X] CHK013 - Is the comparison method specified as byte-exact (not structural / not semantic)? [Clarity, Spec §FR-036, §SC-016, CL-10]
- [X] CHK014 - Is the line-ending normalisation rule (`\r\n` → `\n` applied to BOTH the re-rendered output and the committed file) unambiguous? [Clarity, Spec §FR-036, CL-10]
- [X] CHK015 - Does the spec call out Windows `core.autocrlf=true` as the explicit motivating case for the normalisation rule (so future maintainers do not "optimise" it away)? [Completeness, Spec §FR-036, CL-10]
- [X] CHK016 - Is the failure taxonomy (entry-count mismatch, missing/added rows, field drift, ordering drift, formatting drift) enumerated so reviewers know what the gate covers? [Coverage, Spec §FR-036]

## N/A / Skip Behaviour (Pre-Phase-1 Branches)

- [X] CHK017 - Does the spec define the precise condition that triggers the N/A skip (`docs/test-data/manifest.json` does not yet exist)? [Clarity, Spec §SC-016, CL-10]
- [X] CHK018 - Does the spec require a visible "skip notice" output (not silent success) when the N/A path is taken? [Completeness, Spec §SC-016, CL-10]

## Schema vs MANIFEST.md Column-Subset Alignment

- [X] CHK019 - Does the spec explicitly state that `MANIFEST.md` is an intentional summary view (not a 1:1 surface of every FR-031 field), with `manifest.json` as the authoritative carrier? [Consistency, Spec §FR-031, CL-11]
- [X] CHK020 - Does FR-031 enumerate the 7-column subset surfaced by the renderer (`id`, `path`/`source_shape`, `domain_group`, `persona_bindings`, `pspf`, `licence`, `cultural_review_required`) so the renderer's locked contract is traceable from the requirement? [Completeness, Spec §FR-031, CL-11]
- [X] CHK021 - Has `domain_group` been added to FR-031's enumerated field list with an explicit cross-reference to the PersonaBinding taxonomy (closing the schema/spec/renderer drift)? [Consistency, Spec §FR-031, CL-12]
