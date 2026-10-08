# Constitutional Grounding Reference (Actor Guidance)

This document is the shared constitutional mapping for actor files in this feature.
It reduces drift by centralizing principle references and AU data-sovereignty constraints.

## Current Principle Map

- I. Primacy of Life and Harm Reduction
- II. National Emergency Management Principles
- II-A. AIIMS Functional Alignment
- III. Multi-Hazard, Multi-Agency Design
- IV. Transparency and Auditability
- V. Warning and Public Information
- VI. Evacuation Framework
- VII. Recovery Support
- VIII. Cloud Platform and Infrastructure

## AU Sovereignty and Bounded Inference Carve-out

- AU residency remains mandatory for persistence, telemetry, secrets, audit, and evidence data.
- A non-AU endpoint is only permitted for model-hosting inference when it is listed in the named, version-controlled carve-out registry.
- The carve-out must include model name, region, business justification, approvers, and review date.
- Data minimization at the model gateway is mandatory for prompts and responses sent to non-AU inference endpoints.
- The carve-out does not broaden platform-level AU controls.

## Citation Rule for Actor Files

When actor files mention constitutional constraints, reference this file and the constitution source:

- `.specify/memory/constitution.md`
- `specs/004-actor-github-agents/contracts/constitutional-grounding.md`
