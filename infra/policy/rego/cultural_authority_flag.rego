# Spec 036 / Phase F (T201) — Cultural Authority gate flag-flip OPA policy.
#
# Per FR-RAG-CA-04 + Plan §F-A2.6 + Pass 2 Q-P2-08 (Locked-on flag class):
# the ``feature.cultural_authority_gate.enabled`` flag is "Locked-on in
# prod" — only the ``test`` environment may flip it. Any attempt to flip
# the flag in ``prod`` (or in any non-``test`` environment) is OPA-denied
# at flag-flip time and emits the audit event
# ``cultural_authority_gate_test_disable_attempt``.
#
# The flag is read by the cultural-authority gate
# (``apps/agents/common/cultural_authority_gate.py``); when true (default)
# the gate is active. When false, gate is bypassed — but Constitution VI-C
# forbids bypass in prod, hence this policy.
#
# Loaded by:
#   - tests/integration/test_cultural_authority_flag_lockdown.py (T195)
#   - infra/scripts/verify-feature-flags.ps1 (CD pre-flip gate, T201)
package cultural_authority_flag

# A flag flip is denied when:
#   - the target flag is feature.cultural_authority_gate.enabled
#   - AND the environment is NOT 'test'
#   - AND the requested new_value is False (i.e. the flag is being disabled)
#
# Re-enabling the flag (False → True) is always permitted; only DISABLING
# is locked.

deny_flag_flip[msg] {
    input.flag == "feature.cultural_authority_gate.enabled"
    input.new_value == false
    input.environment != "test"
    msg := sprintf(
        "FR-RAG-CA-04: feature.cultural_authority_gate.enabled is Locked-on in '%v' environment; only 'test' may flip the flag (Pass 2 Q-P2-08; ADR-12).",
        [input.environment],
    )
}

# Helper used by the test harness — returns the audit event that MUST emit
# on a denied flip attempt. The CD pipeline routes this to the AuditWriter
# sink alongside the policy denial.

audit_event[ev] {
    input.flag == "feature.cultural_authority_gate.enabled"
    input.new_value == false
    input.environment != "test"
    ev := {
        "event_type": "cultural_authority_gate_test_disable_attempt",
        "flag": input.flag,
        "requested_value": input.new_value,
        "environment": input.environment,
        "actor_id": input.actor_id,
        "decision": "denied",
    }
}
