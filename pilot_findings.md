# AccessLens DC balanced pilot findings

Run date: 2026-09-01  
Pilot seed: 20260901

## Pilot design

The balanced coverage pilot contains 12 DDOT records: one record from every combination
of three study areas and four historical inventory conditions.

An earlier smoke test queried the first 12 rows of the sorted candidate file. All 12 were
`Fair` records in Anacostia/Fairlawn, so that result is excluded from the headline pilot
finding. The sampling bug was fixed and covered by an automated test.

## Coverage result

- 11 of 12 records returned nearby imagery: 91.7 percent point coverage.
- Anacostia/Fairlawn: 4 of 4 covered.
- Columbia Heights/Petworth: 3 of 4 covered.
- Navy Yard/Capitol Riverfront: 4 of 4 covered.
- The coverage query returned 567 image candidates: 60 panoramas and 507 directional
  images.
- Candidate capture timestamps ranged from 2017-04-08 through 2026-08-24.

Coverage changed for two records between the coverage query and the collection query.
The project therefore treats API coverage as a time-stamped observation and retains the
downloaded evidence used for evaluation.

## Selected image batch

- 22 images were downloaded for 11 records.
- Selected-image dates ranged from 2018-12-28 through 2026-06-26.
- Five selected images are panoramas.
- Every selected view passed the initial distance-and-heading ranking rule, with panorama
  coverage handled separately.

## OpenCV quality screen

- 19 of 22 images passed the provisional resolution, blur, brightness, and contrast gate.
- Three images were rejected for low contrast.
- Visual review found additional semantic failures that simple image statistics do not
  capture, including downward-facing roadway images and views where the target corner is
  not identifiable.

This is evidence for retaining a human view-relevance check alongside numeric image
quality metrics.

## Local model smoke result

The Project Sidewalk DINOv2 validator scored seven images and rejected 15 based on the
provisional deployment policy. At the record level:

- 10 predictions abstained;
- one predicted `ramp_present`;
- one predicted `ramp_absent`.

These are pipeline outputs, not accuracy results. Accuracy, precision, and recall remain
unreported until the blind human labels are complete.

## Decision

The study areas have enough imagery coverage to continue. The current 83.3 percent
record-level abstention rate is an important pilot result. Thresholds will not be relaxed
to manufacture broader coverage before human review.

The next action is to complete the 12-record blind labeling task, adjudicate insufficient
views, and compare the human labels with both the historical inventory baseline and the
local validator.
