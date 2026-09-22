# AccessLens DC project summary

## Short description

Built and ran a curb-ramp inventory QA pilot using DDOT's 34,859-record ADA inventory,
Mapillary street imagery, OpenCV quality checks, and a pinned Project Sidewalk DINOv2
model. The workflow ranks nearby views, records source provenance, creates target-centered
crops, supports blind human labeling, measures model abstention, and sends uncertain or
conflicting records to a review queue.

## Initial pilot

- Balanced 12-location sample across three DC study areas and four inventory conditions
- Current imagery found for 11 locations
- 567 candidate images screened and 22 source images selected
- 19 target-centered crops created
- Two blind human-label passes reconciled across all 12 records
- 9 final scorable records and 3 cannot-determine records
- Target-model coverage increased from 11.1 percent to 77.8 percent
- Target-model answered-case accuracy was 14.3 percent, exposing poor cross-source transfer
- Five inventory-history disagreements retained as unresolved because no 2016 evidence exists
- Cost analysis compares wasted field visits with missed absent ramps at three ratios
- 56 automated tests passing in GitHub Actions

## Scope

The project screens records for review. It does not determine ADA or PROWAG compliance.
Slope, width, grade-break geometry, drainage, and related criteria require calibrated
measurement or field inspection.

## Project walkthrough

I built AccessLens DC to apply computer vision evaluation to a transportation-data
problem. I started with the full DDOT inventory, audited its fields, drew a reproducible
sample, collected licensed street imagery, added image-quality gates, and ran a published
curb-ramp validator locally. The first model run had low coverage because many source
views did not center the target. I added directional cropping and panorama projection,
which raised model coverage from 11.1 percent to 77.8 percent. I then ran a second blind
label pass and adjudicated the one direct conflict before scoring. Final accuracy was
14.3 percent, showing that improved framing solved view eligibility while the pretrained
model still transferred poorly to this Mapillary sample. I kept the failed model result
and documented the data needed for the next evaluation. I also reviewed every inventory
disagreement under a frozen rubric. The current images could not separate world change
from a 2016 inventory error, so I kept all five historical causes unresolved.

## Current status

The initial pilot and disagreement analysis are complete. The scale-up phase has a frozen
72-record development split and 24-record held-out split. Development imagery collection,
target-crop construction, and evidence-quality screening are complete. Blind development
labeling, second-reviewer agreement, model selection or training, settings freeze, and the
single held-out evaluation remain.
