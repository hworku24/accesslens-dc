# AccessLens DC project status

Updated: 2026-09-21

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
- Passed 41 automated tests.

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

## Next scale-up

1. Collect the larger development and held-out batches.
2. Label at least 50 usable records, keeping insufficient imagery as a measured outcome.
3. Add a second reviewer and report agreement.
4. Train or select a model using imagery closer to the Mapillary deployment domain.
5. Run the frozen policy on held-out records.
