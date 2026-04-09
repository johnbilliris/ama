---
name: ama-rubric-grader
description: 'Detailed evaluator for the Azure Master Architect Program rubric that scores criteria, justifies each score using non-.github files, offers five improvements per criterion, totals the score, and maps it to the grade band.'
---

# AMA Rubric Grader

## When to Use This Skill
- Respond with a criterion-by-criterion evaluation whenever someone asks you to score a submission or demo against the Azure Master Architect Program criteria described in [AMA_Rubric_Asia.md](..\..\..\AMA_Rubric_Asia.md).
- Use when the prompt asks for a full rubric assessment, grade bands, improvement ideas, or a holistic score summary.

## Prerequisites
- Access to the rubric file at [AMA_Rubric_Asia.md](..\..\..\AMA_Rubric_Asia.md) as the scoring baseline.
- Ability to read project artifacts that live outside the `.github` folder for evidence supporting each score.
- Clarity on which deliverable (demo, codebase, documentation, etc.) is under review.

## Step-by-Step Workflow
1. Identify the deliverable scope and confirm the rubric categories that need scoring.
2. Search every repository file except those inside `.github/` for evidence tied to each criterion; ignore files under `.github` when gathering input.
3. For each rubric row, assign one of the four score values (Excellent, Good, Satisfactory, Needs Improvement) and explain why the evidence supports that level. Cite files or sections by path when possible.
4. List five concrete improvement opportunities for each criterion so maintainers know exactly what to tackle next.
5. Sum the numeric scores (Excellent=5, Good=4, Satisfactory=3, Needs Improvement=1-2) and map the total to a grade band (A/B/C/D-F) per the rubric guide.
6. Finish the response with the total score, corresponding grade band, and a reminder of the most critical next action or risk.

## Troubleshooting
- **Missing evidence**: If no file contains support for a criterion, explain why the documentation/code falls short and default to Needs Improvement with a note on what to supply.
- **Ambiguous deliverables**: Ask the user to clarify which feature or component they want graded before continuing.
- **Grade band confusion**: Revisit the tally rules in [AMA_Rubric_Asia.md](..\..\..\AMA_Rubric_Asia.md) to ensure the total matches the described grade ranges.

## References
- [AMA_Rubric_Asia.md](..\..\..\AMA_Rubric_Asia.md) - Source rubric definitions and scoring bands.
