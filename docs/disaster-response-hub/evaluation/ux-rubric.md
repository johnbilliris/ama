# UX Evaluation Rubric: Disaster Response Coordination Hub

## Purpose

This rubric provides structured scoring criteria for evaluating the hub's dashboard and operational pages during post-exercise review. It aligns with success criterion SC-007 which requires ≥85% of evaluated users to rate the experience as clear, distinctive, and appropriate for high-pressure decision-making.

## Scoring Scale

| Score | Label | Meaning |
|-------|-------|---------|
| 5 | Excellent | Exceeds expectations — would confidently rely on this in a real incident |
| 4 | Good | Meets expectations — effective and appropriate with minor suggestions |
| 3 | Adequate | Functional but has notable friction or missed opportunities |
| 2 | Poor | Significant issues that would slow decision-making |
| 1 | Unacceptable | Would not use this in an operational setting |

**Pass threshold**: A dimension passes when ≥85% of participants score it ≥4.

## Evaluation Dimensions

### 1. Clarity

*Can the operator quickly understand what the system is showing?*

| Criterion | What to assess |
|-----------|---------------|
| Information hierarchy | Is the most important information (severity, status, actions) visually prominent? |
| Labels and terminology | Do labels align with AIIMS and agency terminology? |
| Status visibility | Are incident status, signal health, and recommendation state immediately clear? |
| Error communication | Are degraded-mode and connectivity issues communicated without confusion? |

### 2. Scanability

*Can the operator find what they need under time pressure?*

| Criterion | What to assess |
|-----------|---------------|
| Visual grouping | Are related items (signals, recommendations, tasks) visually grouped? |
| Page load speed | Does the dashboard render meaningful content within 2 seconds? |
| Progressive disclosure | Is detail available on demand without cluttering the primary view? |
| Mobile readiness | Is all critical information accessible on a tablet or phone layout? |

### 3. Visual Distinctiveness

*Does the design stand out as purpose-built for emergency coordination?*

| Criterion | What to assess |
|-----------|---------------|
| Colour system | Do colours convey severity, status, and trust without ambiguity? |
| Typography | Is text readable at arm's length on large screens and in bright conditions? |
| Component design | Do cards, panels, and banners feel operational rather than generic? |
| Brand coherence | Is the visual style consistent across all pages and states? |

### 4. Decision Confidence

*Does the system help the operator make better decisions?*

| Criterion | What to assess |
|-----------|---------------|
| Provenance visibility | Can the operator see where each signal or recommendation came from? |
| Confidence indicators | Are confidence levels and freshness scores visible for key data? |
| Approval workflow | Is the approve/reject/escalate flow clear and auditable? |
| Alert review | Can the operator preview alert content, audience, and channels before publishing? |

## Administration

- **Timing**: Administer immediately after each exercise scenario, before group debrief
- **Participants**: All operators who actively used the hub during the exercise
- **Coverage requirement**: At least 3 different organisation types and 5 different persona types
- **Data capture**: Use the companion `post-exercise-survey.md` form
- **Analysis**: Aggregate per dimension; overall pass requires all 4 dimensions at ≥85% ≥4-rated
