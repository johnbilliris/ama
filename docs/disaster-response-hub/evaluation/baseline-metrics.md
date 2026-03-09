# Baseline Metrics: Disaster Response Coordination Hub

## Purpose

This document defines the pre-hub baseline measurements for success criteria SC-004 through SC-007. Each metric is captured per scenario type, jurisdiction, and participating organisation set during a tabletop or exercise run **without** the hub, then compared against the same exercise run **with** the hub.

## SC-004: Coordinated Response Time

**Definition**: The elapsed time from incident activation to the first cross-agency coordinated action plan being visible to all participating organisations.

| Metric | Measurement | Capture Method |
|--------|-------------|----------------|
| Time to first coordinated action | Minutes from activation timestamp to first visible cross-agency plan | Exercise facilitator timestamp log |
| Baseline target | Current documented process time per jurisdiction | Pre-exercise tabletop recording |
| Hub target | ≥50% improvement over baseline | Hub audit trail timestamps |

### Baseline capture procedure
1. Run the standard tabletop exercise for the selected scenario and jurisdiction
2. Record the activation timestamp (T₀) when the incident is formally declared
3. Record the timestamp (T₁) when the first coordinated action plan is communicated to all agencies
4. Baseline = T₁ - T₀

## SC-005: Evacuation Decision Timing

**Definition**: The elapsed time from incident activation to the first at-risk population evacuation decision meeting the authority threshold.

| Metric | Measurement | Capture Method |
|--------|-------------|----------------|
| Time to evacuation decision | Hours from activation to authorised evacuation decision | Exercise facilitator timestamp log |
| Baseline target | Current documented decision timing per scenario | Pre-exercise tabletop recording |
| Hub target | ≥24 hours earlier than baseline | Hub recommendation + approval timestamps |

### Baseline capture procedure
1. Run the scenario with the current manual coordination process
2. Record when evacuation-relevant information first reaches the decision-maker
3. Record when the evacuation decision is formally authorised
4. Baseline = authorisation timestamp - activation timestamp

## SC-006: Resource Deployment Efficiency

**Definition**: A composite of time-to-assignment, resource-utilization ratio, and unfilled-priority-request count.

| Metric | Measurement | Capture Method |
|--------|-------------|----------------|
| Time-to-assignment | Minutes from resource request to assignment confirmation | Task status timestamps |
| Resource-utilization ratio | Assigned resources / available resources | Post-exercise audit |
| Unfilled priority requests | Count of high/critical requests unmet at exercise end | Task status review |
| Hub target | ≥30% improvement over baseline composite | Hub task and recommendation audit trail |

### Baseline capture procedure
1. During the baseline exercise, track each resource request and its resolution
2. Calculate the three component metrics
3. Compute a weighted composite: `0.4 × time-to-assignment + 0.3 × utilization + 0.3 × unfilled-reduction`

## SC-007: UX Evaluation

**Definition**: Post-exercise survey results from participants rating the dashboard and key operational pages.

| Metric | Measurement | Capture Method |
|--------|-------------|----------------|
| Clarity score | 5-point Likert scale | Post-exercise survey |
| Scanability score | 5-point Likert scale | Post-exercise survey |
| Visual distinctiveness score | 5-point Likert scale | Post-exercise survey |
| Decision confidence score | 5-point Likert scale | Post-exercise survey |
| Overall pass threshold | ≥85% rate as clear/distinctive/appropriate (≥4 on each axis) | Survey aggregation |
| Participant coverage | ≥3 org types, ≥5 persona types | Participant roster |

See `ux-rubric.md` and `post-exercise-survey.md` for the detailed instruments.

## Exercise Pack Structure

Each evaluation exercise pack contains:
1. **Scenario definition** — hazard type, jurisdiction, timeline, injected signals
2. **Participant roster** — organisations, personas, roles for coverage validation
3. **Baseline recording sheet** — timestamps and metrics per the procedures above
4. **Hub-enabled recording sheet** — same metrics captured through the hub audit trail
5. **Comparison report template** — side-by-side baseline vs. hub results per SC
