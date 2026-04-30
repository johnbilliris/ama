# MAF middleware — adding a cross-cutting policy in one place (SC-005 worked example)

This README is the **canonical worked example** for spec-033's SC-005:

> *"Mean time to add a new cross-cutting policy (e.g., a new content-safety
> category, a new audit field) drops to a single change applied centrally
> rather than five per-agent changes — verified by a worked example during
> the feature."*

## Adding a new content-safety category

To block a new category of content (e.g., "extremist-recruitment-language")
across **all five agents** at once, edit only this file:

`apps/agents/maf_runtime/middleware/content_safety_middleware.py`

```diff
 from common.content_safety import ContentSafetyValidator

 from ..errors import PolicyFailure
+
+# T-XXXXX — block extremist-recruitment-language category platform-wide.
+_NEW_BLOCKED_CATEGORIES: tuple[str, ...] = ("extremist_recruitment",)
```

…then in `process(...)`, after the existing `validator.validate(...)` call,
add:

```diff
         result = self._validator.validate(text=text, max_length=self._max_input_length)
+        for cat in _NEW_BLOCKED_CATEGORIES:
+            if cat.lower() in text.lower():
+                result.passed = False
+                result.reason = f"blocked_by_category:{cat}"
+                result.result = "failed_with_fallback"
+                break
         if not result.passed:
```

That's the entire change. **No edit is required to any of the five named
agents** (`monitoring_agent.py`, `risk_assessment_agent.py`, etc.) because
they all bind `ContentSafetyMiddleware` via the foundational chain in
`agents/_factory.py::build_middleware_chain(...)`.

## Verifying the change applies uniformly

Run the per-agent equivalence harness — it MUST still PASS for every agent
because no agent-side code changed:

```bash
pytest tests/equivalence -q
```

A `FAIL` here would mean the new policy changed an agent's categorical decision
on the corpus. That's a real signal — investigate before proceeding.

## Adding a new audit field

Add the field to `apps/agents/maf_runtime/middleware/audit_middleware.py`'s
`_AuditContext` dataclass and to the dict written by `process(...)`. The
audit-entry schema (`specs/033-maf-adoption/contracts/audit-entry.schema.json`)
should also be updated to mention the new field — but the field-snapshot
regression test (T009b) only fails on **removed** fields, so additions are
backward-compatible.

## Adding a new OTel span attribute

Add a `_set_attribute(span, "...", value)` call inside
`apps/agents/maf_runtime/middleware/otel_middleware.py::process(...)`. Every
agent's spans pick it up automatically.

## SC-010 cross-reference

The "sixth named agent" worked example (SC-010) is in
`tests/integration/no_op_agent/test_no_op_inherits_middleware.py`. It proves
that adding an Agent Definition + a 10-line module suffices — no new
middleware, telemetry, audit, or workflow-runtime code is required.
