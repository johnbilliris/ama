# Safety guardrails policy
# Enforced by OPA/Gatekeeper on the API control plane before any
# safety-critical action (public alerts, evacuation recommendations).

package drh.safety_guardrails

import rego.v1

# ── Public alert publishing must have commander approval ──

deny contains msg if {
    input.action == "publish_alert"
    not input.approval_decision
    msg := "Public alert cannot be published without an approval decision."
}

deny contains msg if {
    input.action == "publish_alert"
    input.approval_decision.outcome != "approved"
    msg := sprintf("Alert blocked: approval outcome is '%s', must be 'approved'.", [input.approval_decision.outcome])
}

# ── Alert must have non-empty content ──

deny contains msg if {
    input.action == "publish_alert"
    not input.alert.content_blocks.headline
    msg := "Alert must include a headline before publishing."
}

# ── Evacuations require high-confidence signals ──

deny contains msg if {
    input.action == "execute_recommendation"
    input.recommendation.type == "evacuation"
    input.recommendation.confidence_level != "high"
    msg := sprintf("Evacuation blocked: confidence is '%s', must be 'high'.", [input.recommendation.confidence_level])
}

# ── Degraded-mode recommendations stay under_review ──

deny contains msg if {
    input.action == "execute_recommendation"
    input.degraded_mode == true
    input.recommendation.status != "under_review"
    msg := "Recommendation must remain under_review when system is in degraded mode."
}

# ── All safety-critical actions require an authenticated persona ──

deny contains msg if {
    input.action in {"publish_alert", "execute_recommendation", "supersede_alert"}
    not input.persona_id
    msg := "Safety-critical action requires an authenticated persona."
}
