# Sprint 2: pilot labeling and evaluation


Completed: 2026-09-01  
Evaluation seed: 20260901

## Outcome

The balanced 12-record pilot is complete. Eight records have adjudicated image-based
presence labels and four are `cannot_determine`, producing an imagery-insufficient rate
of 33.3 percent.

## Model comparison

| Model | Answered | Coverage | Precision | Recall | F1 | Accuracy | 95% accuracy interval | Mean latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DDOT 2016 inventory baseline | 8/8 | 100.0% | 50.0% | 100.0% | 66.7% | 62.5% | 30.6% to 86.3% | 0 ms |
| Project Sidewalk DINOv2 validator | 1/8 | 12.5% | not estimable | not estimable | not estimable | 100.0% | 20.6% to 100.0% | 16.1 ms |

The validator answered one scorable record correctly. Its 100 percent answered-case
accuracy is not evidence of deployment performance because coverage was 12.5 percent
and the accuracy interval spans 20.7 to 100 percent. Precision, recall, and F1 cannot be
estimated from the single negative decision.

## Inventory disagreements

Three of eight scorable records disagreed with the 2016 inventory baseline:

- `ADA_CurbRampPt_18645`: inventory `Fair` implied `ramp_present`, while current imagery was labeled `ramp_absent`.
- `ADA_CurbRampPt_3245`: inventory `Fair` implied `ramp_present`, while current imagery was labeled `ramp_absent`.
- `ADA_CurbRampPt_23006`: inventory `Non-Compliant` implied `ramp_present`, while current imagery was labeled `ramp_absent`.

These are review candidates. They do not prove an inventory error or physical world
change without an independent source or field inspection.

## Adjudication

- Raw labels received: 12
- Labels changed by the written evidence rule: 1
- Imagery insufficient: 4
- Possible world-change or inventory-review candidates: 3
- Ambiguous geometry or model abstention: 4
- Records with full agreement: 1

`ADA_CurbRampPt_28492` was changed from `ramp_absent` to `cannot_determine` because the
human quality field was `unusable`. The raw export remains unchanged and the adjudicated
copy records the reason.

## Frozen pilot policy

- OpenCV gate: minimum 640 by 480, blur variance 60, brightness 35 to 220, contrast 25.
- Validator positive threshold: 0.70.
- Validator negative threshold: 0.30.
- Maximum directional heading difference: 35 degrees.
- Maximum camera distance: 35 meters.
- Panoramas abstain until a directional projection step is implemented.

The thresholds are frozen for the next evaluation batch. The high abstention rate will
not be reduced by tuning on held-out records.

## Sprint decision

The historical inventory remains useful as a high-recall baseline, with 62.5 percent
pilot accuracy and three false-positive presence assumptions. The cross-source validator
is not ready for deployment because its conservative eligible-view coverage is too low.
The next sprint should improve target-centered view construction, preserve the current
thresholds for held-out evaluation, and expand the labeled sample.
