# Operator Runbooks: Disaster Response Coordination Hub

## Runbook 1: Activating a New Incident

### When to use
A new disaster event is confirmed or upgraded to trigger multi-agency coordination.

### Steps

1. **Create the incident** via the API or seeded scenario:
   - POST `/api/signals` with the initial authoritative warning (e.g. BoM severe weather)
   - The ingestion service auto-creates the incident if the `incidentId` matches a new event
2. **Verify the dashboard**:
   - Navigate to `/incidents/{incidentId}`
   - Confirm: participating organisations, severity, jurisdiction, and signal summary appear
3. **Assign personas**:
   - Ensure all participating agencies have active personas mapped to the incident
   - Verify via GET `/api/personas/{personaId}/workspace` that tasks are visible
4. **Monitor signal health**:
   - Check the Source Health Panel for authoritative vs. community signal counts
   - If contradicted signals appear, the Degraded Mode Banner will activate automatically

### Escalation
If the dashboard does not load within 30 seconds, check the API health endpoint at `/api/health` and review Application Insights for errors.

---

## Runbook 2: Processing a Recommendation and Publishing a Public Alert

### When to use
The risk assessment agent has generated a recommendation requiring incident commander approval.

### Steps

1. **Review the recommendation** on the incident dashboard:
   - Check the recommendation summary, explanation, and supporting signal IDs
   - Verify confidence level is appropriate for the action type
2. **Record an approval decision**:
   - POST `/api/recommendations/{recommendationId}/approvals` with:
     - `approverPersonaId`: The authenticated commander persona
     - `outcome`: `approved`, `rejected`, or `escalated`
     - `rationale`: Free-text explanation (required by safety guardrails)
3. **Publish the alert** (if recommendation is a `public_alert` type):
   - The approval automatically creates an alert in `approved` status
   - Apply a delivery template if needed: POST `/api/alerts/{alertId}/template`
   - Publish: POST `/api/alerts/{alertId}/publish`
   - Deliver to channels: POST `/api/alerts/{alertId}/deliver`
4. **Verify delivery**:
   - Check the delivery response for channel-specific confirmation payloads
   - The alert status in the dashboard should show "published"

### Safety checks
- The OPA safety guardrails policy blocks publishing without an approval decision
- The publish validation rejects alerts missing a headline or channel set
- Evacuation recommendations require `high` confidence level

---

## Runbook 3: Responding to Degraded Mode

### When to use
The system detects contradicted signals, offline data sources, or circuit breaker trips.

### Steps

1. **Identify the degradation**:
   - The Degraded Mode Banner on the dashboard shows the count of contradicted/degraded signals
   - The API response header `X-Degraded-Mode: true` indicates backend circuit breaker activation
2. **Assess impact**:
   - Recommendations generated during degraded mode are automatically held in `under_review` status
   - The recommendation guardrails service adds `requiresManualReview: true` to affected items
3. **Manual review**:
   - Each held recommendation must be individually reviewed by the incident commander
   - Provide additional rationale when approving during degraded mode
4. **Recovery**:
   - When data sources recover and the circuit breaker resets, the `X-Degraded-Mode` header clears
   - New recommendations will flow through normal confidence-based approval

---

## Runbook 4: Running a Preparedness Rehearsal

### When to use
Before live disaster season, or when onboarding new agencies/jurisdictions.

### Steps

1. **Navigate to** `/preparedness`
2. **Review the organisation catalog** to verify agencies are correctly seeded for the target jurisdiction
3. **Review the framework catalog** to confirm AIIMS and communications frameworks are assigned
4. **Select a scenario type** (flood, bushfire, or cyclone) and click "Run rehearsal replay"
5. **Review findings**:
   - The Findings panel shows multi-agency coverage and framework assignment analysis
   - The Coordination Gaps panel highlights missing capabilities or insufficient coverage
6. **Address gaps**:
   - If gaps are found, update seed data and framework assignments
   - Re-run the rehearsal to verify resolution

### Validation criteria
- At least 2 organisations available per jurisdiction
- At least 1 communications framework assigned for public messaging rehearsal
- Cyclone scenarios should include commonwealth meteorology support

---

## Runbook 5: Cross-Agency Task Coordination

### When to use
During an active incident when multiple agencies have interdependent tasks.

### Steps

1. **Check the workspace** at `/workspaces/{personaId}`
2. **Review assigned tasks**: Each task shows priority, status, and dependency chain
3. **Update task status**:
   - POST `/api/tasks/{taskId}/status` with the persona ID and new status
   - Only the assigned persona or same-organisation members can update
4. **Monitor dependencies**:
   - The Dependencies panel shows tasks from other agencies that block your work
   - Cross-agency task updates are propagated via the dependency notifier

### Access control
- Cross-agency task status updates are rejected with HTTP 403
- Only incident commanders and planning officers can view tasks across organisations
