# AccessLens DC pilot memo

Date: 2026-09-21  
Status: Draft pending target-crop label adjudication

## Decision

AccessLens DC can organize curb-ramp inventory records, street imagery, image-quality
checks, model decisions, and human review in one repeatable workflow. The current pilot
does not support operational deployment or compliance decisions. The next decision is
whether to fund a larger labeled evaluation after the second pilot label pass is
resolved.

## Question

Can licensed street imagery and a pretrained vision model help transportation staff
screen DDOT curb-ramp inventory records for human review?

## Data and method

- Audited 34,859 DDOT ADA curb-ramp point records.
- Confirmed that every record lists `YEAR_INSPECTED = 2016`.
- Retained nulls and undocumented status codes in the audit.
- Selected three DC study areas.
- Drew a seeded, balanced sample across Good, Fair, Missing, and Non-Compliant inventory
  conditions.
- Queried Mapillary for licensed street imagery and retained capture and source metadata.
- Applied OpenCV checks for resolution, blur, brightness, and contrast.
- Ran a pinned Project Sidewalk DINOv2 curb-ramp validator locally on CPU.
- Used present, absent, and cannot-determine human labels.
- Treated model abstention and insufficient imagery as measured outcomes.

The Project Sidewalk model file, revision, hashes, preprocessing steps, probability
thresholds, and image-selection rules are recorded in the repository.

## Pilot evidence

| Measure | Result |
|---|---:|
| Balanced pilot records | 12 |
| Locations with Mapillary coverage | 11 of 12 |
| Candidate Mapillary images returned | 567 |
| Source images selected | 22 |
| Source images passing OpenCV checks | 19 of 22 |
| Target-centered crops produced | 19 |
| Target-centered crops passing crop checks | 16 of 19 |
| Target-model decisions | 8 of 12 |
| Target-model abstentions | 4 of 12 |
| Target model versus inventory disagreements | 2 |

The Sprint 2 source-view evaluation produced eight scorable human labels and four
cannot-determine labels. The DDOT inventory baseline achieved 62.5 percent accuracy on
those eight records. The source-view Project Sidewalk arm answered one of eight scorable
records, which is 12.5 percent coverage. Its one correct answer cannot support a model
performance claim.

Target-centered crops raised answered-case coverage. Visual review also found that the
new framing could change a human label. Accuracy from the target-centered arm remains
withheld until the blind second pass and conflict adjudication are complete.

## Review queue

Two target-centered model decisions disagree with the inventory-derived presence label.
They are review candidates. A disagreement can result from world change, inventory age,
view geometry, image quality, model error, or label error. Independent evidence is
required before changing an inventory record.

## Limits

- Twelve locations are too few for a general performance estimate.
- One reviewer completed the first label pass.
- Street imagery coverage and view quality vary by neighborhood and capture source.
- The pretrained model was developed for a related curb-ramp validation task and may not
  transfer cleanly to Mapillary views in Washington, DC.
- Monocular imagery cannot measure running slope, cross slope, clear width, grade breaks,
  drainage tolerances, or other ADA and PROWAG criteria.
- The DDOT layer lacks usable intersection identifiers, and its status codes have no
  documented meaning in the downloaded data.

## Next work

1. Complete the remaining 11 blind target-crop labels.
2. Reconcile both label passes under the frozen adjudication protocol.
3. Publish final pilot accuracy, coverage, abstention, and conflict counts.
4. Expand to at least 50 usable labeled locations across the frozen strata.
5. Separate development and held-out records before further threshold changes.
6. Add a second reviewer and report agreement.

## Recommendation

Finish the blind adjudication pass before citing target-model accuracy. If the workflow
remains useful after conflict review, proceed to a larger labeled evaluation. Keep the
output framed as a review queue and preserve professional inspection for compliance
decisions.
