# AccessLens DC project status

Updated: 2026-09-01

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
- Passed 28 automated tests.

## Sprint 2 result

- Eight records were scorable and four were imagery-insufficient.
- The DDOT baseline achieved 62.5 percent accuracy with 100 percent coverage.
- The Project Sidewalk validator answered one of eight scorable records, for 12.5 percent
  coverage. Its single correct answer is insufficient for a performance claim.
- Three historical inventory records entered the qualified review queue.

## Sprint 3 next run

1. Implement target-centered directional crops and panorama projection.
2. Collect the larger development and held-out batches.
3. Label at least 50 usable records, keeping insufficient imagery as a measured outcome.
4. Run the frozen policy on held-out records.
5. Generate the final result map, review queue, and stakeholder memo.

## Final artifacts still to produce

- coverage report;
- completed human-label sheet and self-agreement result;
- model comparison table;
- adjudicated disagreement log;
- result map and review queue;
- two-page stakeholder memo and project summary.
