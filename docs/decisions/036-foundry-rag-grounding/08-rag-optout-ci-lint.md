# ADR 08 — RAG Opt-Out: CI Lint Mechanism (Meta-ADR)

**FR**: FR-RAG-NS-08
**Persona memo citation**: `personas-input/technical-quality.md` §"opt-outs are intentional and auditable"
**Approver**: AMA Spec-036 Architecture Review (J.B., Lead Architect) + Quality SRE
**Date**: 2026-05-08
**Status**: Accepted

**Code-marker optional**: true

## Context

The other eight RAG-OPTOUT ADRs (FR-RAG-NS-01..07, FR-RAG-NS-09) document **why** specific call sites bypass RAG. Without an enforcement mechanism, the documentation drifts: a refactor introduces a new opt-out without an ADR, or an ADR lingers after its call site has been re-grounded.

This ADR documents the **mechanism** that prevents drift:

* a CI lint step (`tools/lint/check_rag_optout_bindings.py`) that walks every Python module under `apps/agents/` and `apps/api/app/services/`,
* extracts every `# RAG-OPTOUT [FR-RAG-NS-NN]` marker,
* asserts each marker has a matching ADR file,
* asserts each ADR (except this one) is referenced by ≥ 1 marker **OR** carries a `code_marker_optional: true` front-matter line (for carve-outs whose call site is implicit, e.g., the Dependency Notifier ADR).

The lint is a blocking CI step; a missing-ADR or orphan-ADR fails the build.

## Decision

The lint mechanism is itself a "non-RAG path" — the lint script does not invoke an LLM. This meta-ADR exists so the FR-RAG-NS-08 entry in the spec maps to a concrete authority, and so the lint script's design choices (canonical regex, allowlist, marker-optional front-matter) are explicit.

## Audit-log shape

The lint emits CI-stdout findings and a non-zero exit code on drift. There is no AMA `AuditRecord` because there is no LLM call.

## Code-comment marker

This ADR is the **meta-ADR for the lint itself**; no code marker is associated with it. The `code_marker_optional: true` front-matter line tells the lint to skip "ADR-08 has no marker" as a finding.

## Consequences

* **Preserves**: opt-out auditability, ADR ↔ code coherence, quality-gate guarantees on every PR.
* **Precludes**: silent drift between code and decision documentation.
* **Tooling**: the lint script lives in `tools/lint/check_rag_optout_bindings.py` and is unit-tested via `tests/contract/test_rag_optout_lint.py`. Wired into `.github/workflows/ci.yml` as the `rag-optout-binding-lint` step.
