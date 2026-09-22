# AccessLens DC project status

Updated: 2026-09-22

## Completed

- Froze evaluation protocol version 1.0 before real model scoring.
- Downloaded, hashed, and audited all 34,859 DDOT inventory records.
- Defined three study areas and generated 144 reproducible, balanced candidates.
- Built Mapillary coverage, ranking, provenance, and collection code.
- Built a protected label contract and imagery attachment workflow.
- Built an OpenCV quality gate with explicitly provisional thresholds.
- Downloaded and hashed the pinned Project Sidewalk ONNX validator.
- Verified local CPU inference.
- Built inventory baseline and model evaluation with abstention, condition slices,
  Wilson intervals, population reweighting, and review queues.
- Generated an interactive candidate map.
- Ran a balanced 12-record Mapillary pilot with 91.7 percent point coverage.
- Downloaded and audited 22 pilot images across 11 records.
- Built and browser-tested a blind local labeling interface.
- Completed and adjudicated all 12 pilot labels.
- Scored the DDOT inventory baseline and Project Sidewalk validator.
- Froze the pilot quality, view-eligibility, and probability thresholds.
- Produced the Sprint 2 model comparison and disagreement report.
- Built target-centered directional crops and panorama projections with retained source
  and crop hashes.
- Audited 19 target-centered crops and ran the pinned Project Sidewalk model on them.
- Built and browser-tested a separate blind target-crop adjudication interface.
- Generated the pilot screening map with coverage, decisions, abstentions, and qualified
  inventory-model disagreements.
- Drafted the stakeholder memo and project summary.
- Added a post-label pipeline that validates the export, compares blind passes, requires
  written reasons for direct conflicts, writes resolved truth, and reruns all model arms.
- Added automatic refresh of the resolved result map and final stakeholder memo.
- Added a GitHub Actions workflow for the full Python test suite.
- Completed the blind target-crop label pass and reconciled all 12 records.
- Adjudicated one direct label conflict with a written reason.
- Wrote final Sprint 3 metrics, result map, review queues, stakeholder memo, and project
  summary.
- Built the Sprint 4 inventory-history adjudication interface for five disagreements.
- Kept all five historical causes unresolved because only post-2016 evidence is available.
- Produced a 14-unit QA split with 6 model errors and 8 imagery-insufficient cases.
- Added field-review cost sensitivity at 1x, 5x, and 10x missed-ramp cost ratios.
- Completed the cited decision memo and project walkthrough.
- Passed 48 automated tests.
- Froze a balanced 72-record development split and 24-record held-out split.
- Excluded all 12 pilot records from both scale-up splits.
- Queried coverage metadata for both splits while keeping held-out images sealed.
- Added resumable Mapillary coverage and image collection with checkpoint files.
- Collected 121 development images across 61 records.
- Built 95 target crops and retained 88 that passed the frozen crop gate.
- Prepared a blind development labeling batch with 55 usable records.

## Sprint 2 result

- Eight records were scorable and four were imagery-insufficient.
- The DDOT baseline achieved 62.5 percent accuracy with 100 percent coverage.
- The Project Sidewalk validator answered one of eight scorable records, for 12.5 percent
  coverage. Its single correct answer is insufficient for a performance claim.
- Three historical inventory records entered the qualified review queue.

## Sprint 3 result

- Five of 12 blind labels agreed exactly across the two view sets.
- Six records had one scorable pass and one cannot-determine pass.
- One present-versus-absent conflict required manual adjudication.
- The resolved truth set contains nine scorable and three cannot-determine records.
- The DDOT inventory baseline achieved 44.4 percent accuracy at 100 percent coverage.
- The source-view model answered one of nine scorable records, for 11.1 percent coverage.
- Target-centered framing raised model coverage to 77.8 percent.
- The target-centered model achieved 14.3 percent answered-case accuracy, with a 95
  percent interval of 2.6 to 51.3 percent.

The framing change improved eligibility but did not solve cross-source model transfer.
The published Project Sidewalk validator is unsuitable for this Mapillary pilot without
new training data or a different model.

## Sprint 4 result

- Five inventory-truth disagreements received record-specific historical-cause review.
- All five remain unresolved because the available captures date from 2019 through 2025.
- Six answered target-model predictions disagreed with resolved human truth.
- Three records remained insufficient for a current present or absent label.
- The source-view policy avoided missed absent ramps by sending all nine scorable records
  to field review.
- The inventory baseline and target-centered policy each missed five of seven absent ramps.
- The ship decision keeps the evidence workflow and rejects automated model clearance.

## Next scale-up

1. Complete blind labels for the 72 development records.
2. Keep the 17 evidence failures as `cannot_determine` outcomes.
3. Add a second reviewer and report agreement.
4. Train or select a model using imagery closer to the Mapillary deployment domain.
5. Freeze preprocessing and decision settings in a code revision.
6. Open held-out imagery and run the frozen policy once.

## Sprint 5 checkpoint

- Development Mapillary coverage: 65 of 72 records, or 90.3 percent.
- Held-out Mapillary coverage metadata: 20 of 24 records, or 83.3 percent.
- Downloaded development evidence: 121 images across 61 records.
- Eligible target evidence: 88 crops across 55 records.
- Evidence failures retained in the labeling batch: 17 records.
- Held-out image downloads: zero.

See `outputs/sprint5_coverage_report.md`, `outputs/sprint5_readiness_report.md`, and
`outputs/scaleup_development_labeling_app.html`.
