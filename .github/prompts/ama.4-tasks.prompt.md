---
description: "Break a plan into heavily detailed, actor-agent-aware tasks with tools and success criteria"
name: "ama.4-tasks"
argument-hint: "Optional: path to plan.md or feature directory to break down"
agent: "speckit.tasks"
---

Break the plan into heavily detailed tasks.

For each task:

- Identify which actor-specific agent(s) are required and involved in the input and output process. Solicit responses from those agents whenever needed — their input and output is valuable.
- Identify the specific tools required to complete the task, chosen from: `execute`, `read`, `edit`, `search`, `web`, `agent`, `todo`.
- Make the task actionable (imperative, single-outcome, unambiguous).
- Include clear, verifiable success criteria.
