# azd up Smoke Template (operator-only — T-AA219 [deferred-to-deploy-step])

> spec-038 final integration smoke. Run from a clean environment.

```pwsh
$env:AZURE_LOCATION = "australiaeast"
azd auth login
azd up
```

Capture the full log under `docs/runbooks/help/azd-up-smoke-{YYYY-MM-DD}.log`.

## Smoke checks (operator)
1. Visit `/help` — landing tiles render per IdP persona claims.
2. Open Help chat — ask "How do I escalate to support?" — verify
   - response streams via SSE,
   - ≥1 citation badge present,
   - audit row in `chat_audit_log` carries `redaction_occurred=false`.
3. Ask "What stocks should I buy?" — verify refusal with
   `expected_refusal=out_of_scope`.
4. Submit a user input containing an email — verify redaction notice in
   UI; audit log carries `user_input_redacted="[REDACTED]"`.
5. Toggle network offline — verify cached articles still load and chat
   banner shows "Chat unavailable — please contact support".
6. Trigger snapshot publish (`gh workflow run help-snapshot.yml`); after
   completion run rollback per `snapshot-publish-rollback.md`.

## Sign-off
Operator records pass/fail per step; if any fail, file an incident and
do NOT proceed to release sign-off (T-AA226).
