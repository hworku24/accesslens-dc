# Output artifacts

This directory contains generated evaluation artifacts and retained historical checkpoints.

## Current review artifacts

- `project_summary.md`: concise project scope, pilot findings, and current scale-up status.
- `stakeholder_memo.md`: pilot decision memo with model, disagreement, cost, and scope analysis.
- `sprint5_coverage_report.md`: scale-up imagery coverage by split, area, and condition.
- `sprint5_readiness_report.md`: development evidence readiness and held-out separation status.
- `scaleup_development_labeling_app.html`: local blind-labeling interface for the development split.

## Pilot and historical checkpoints

- `sprint2_pilot_report.md`: initial source-view evaluation.
- `sprint3_pilot_report.md`: target-centered pilot evaluation and reconciled-label results.
- `sprint4_adjudication_report.md`: disagreement and historical-cause review.
- `sprint4_screening_costs.md`: field-review sensitivity analysis.
- `sprint4_project_walkthrough.md`: technical walkthrough of findings, limits, and next steps.
- `stakeholder_memo_sprint3.md`: retained Sprint 3 checkpoint before the final Sprint 4 memo.

## Machine-readable and interactive outputs

CSV and JSON files preserve predictions, metrics, review queues, and adjudication records.
HTML files provide maps and local review interfaces. Model-specific directories retain cached
pilot outputs so published results can be reproduced without rerunning inference.

The canonical current status is `PROJECT_STATUS.md` at the repository root. Historical
artifacts are retained for auditability and should not be interpreted as the latest project
state.
