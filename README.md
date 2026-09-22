# AccessLens DC

AccessLens DC evaluates whether current, licensed street imagery and a pretrained
computer-vision model can identify DDOT curb-ramp inventory records that deserve human
review.

The project uses the District's 2016 ADA curb-ramp inventory as a historical baseline,
Mapillary as the current-imagery source, human image labels as evaluation truth, OpenCV
for image-quality screening, and a pinned Project Sidewalk DINOv2 validator for local
inference.

## Decision this project supports

The output is a prioritized QA queue for transportation staff. It can flag a ramp that
appears present, appears absent, is impossible to judge from available imagery, or
disagrees with the historical inventory.

It does not calculate slope, width, grade-break geometry, drainage tolerances, or legal
ADA/PROWAG compliance. Those decisions require calibrated measurement, LiDAR, field
inspection, or qualified professional review.

## What already works

- Pinned DDOT GeoJSON with SHA256 and a field-level data audit.
- 34,859 real inventory points profiled without dropping nulls silently.
- Three defined DC study areas and 144 seeded, stratified coverage candidates.
- Mapillary coverage lookup, view ranking by distance and heading, image download, and
  durable provenance manifest.
- Protected human-label sheet with `ramp_present`, `ramp_absent`, and
  `cannot_determine` truth states.
- OpenCV blur, brightness, contrast, and resolution gate.
- Pinned 24 MB Project Sidewalk quantized DINOv2 ONNX model running locally on CPU.
- DDOT inventory baseline, abstention-aware model scoring, Wilson 95 percent confidence
  intervals, per-condition results, and population reweighting.
- Interactive map of the candidate sample.
- Automated tests for data audit, geographic logic, image ranking, QA policy, aggregation,
  and evaluation.

## Headline data findings

- The downloaded layer contains 34,859 point records.
- Every record reports `YEAR_INSPECTED = 2016`.
- `INTERSECTION_ID` is null for every record and cannot support intersection grouping.
- `ESTIMATED_YEAR_OF_IMPROVEMENT` is 2030 for every record.
- `STATUS` is retained as an undocumented code and excluded from semantic claims.
- Population reweighting uses the four documented non-null inventory conditions: Good,
  Non-Compliant, Fair, and Missing. Those categories contain 34,682 records; the remaining
  177 records are excluded from condition-weighted calculations but remain in the full
  inventory audit.

See `data_notes.md` for counts, bounds, nulls, duplicate checks, timestamps, and the
source-file hash.

## Repository layout

```text
accesslens-dc/
├── config/                    Frozen and provisional policy settings
├── data/
│   ├── labels/                Protected human-label data
│   ├── processed/             Audits, samples, and imagery manifests
│   └── raw/                   Pinned DDOT source download
├── docs/                      Domain, architecture, protocol, and model notes
├── outputs/                   Maps, metrics, predictions, and review artifacts
├── src/curb_ramp_eval/        Reusable project code
├── tests/                     Automated verification
├── eval_protocol.md           Evaluation policy frozen before model results
└── PROJECT_STATUS.md          Current project checkpoint
```

## Evaluation history

`eval_protocol.md` preserves the version 1.0 design written before real model scoring.
The implementation later used a 144-record three-area coverage pool, a balanced 12-record
pilot, and a separately frozen 72-development/24-held-out scale-up split. The original
protocol is intentionally retained unchanged; `docs/protocol-evolution.md` documents how
the later sampling and evaluation stages relate to it.

## Reproduce the completed foundation

```bash
python3 audit_inventory.py
python3 make_coverage_sample.py
python3 make_candidate_map.py
python3 -m unittest discover -s tests -v
```

Open `outputs/candidate_map.html` to inspect the sampled locations.

## Continue with Mapillary

Create a Mapillary developer token and keep it in your local shell:

```bash
export MAPILLARY_ACCESS_TOKEN='your-token-here'
python3 make_pilot_sample.py
python3 check_mapillary_coverage.py \
  --candidate-file data/processed/mapillary_pilot_candidates.csv \
  --output-file data/processed/mapillary_pilot_coverage_results.csv
python3 collect_mapillary_imagery.py \
  --candidate-file data/processed/mapillary_pilot_candidates.csv \
  --manifest-file data/processed/mapillary_pilot_image_manifest.csv \
  --image-root data/images/mapillary_pilot
python3 attach_images_to_labels.py
```

You can also copy `.env.example` to `.env` and place the token there. `.env` is ignored
by version control. Coverage checks checkpoint progress and retry timeout, connection,
rate-limit, and common transient server failures.

## Run the local model

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python download_project_sidewalk_model.py
.venv/bin/python audit_image_quality.py
.venv/bin/python run_project_sidewalk_validator.py
```

The model revision and downloaded file hashes are stored under the ignored `weights/`
directory. The Project Sidewalk model's published class-0 output is stored as
`validator_correct_probability`; it is not presented as a calibrated physical
curb-ramp-presence probability. See `docs/model-provenance.md`.

## Label and evaluate

The evaluation keeps `cannot_determine` and model abstention as measured outcomes rather
than silently discarding them. Screening prediction files are evaluated one model at a
time, preventing records from different model arms from overwriting each other.

The DDOT baseline maps `Missing` to `ramp_absent` and Good, Fair, or Non-Compliant to
`ramp_present`. It is scored against current human-reviewed imagery, so disagreements
remain candidates for investigation, not claims that the historical inventory is wrong.

## Evidence standard

The frozen protocol, source hashes, model revision, raw per-image scores, abstentions,
and disagreement records are retained. Failures and coverage limitations are reported
alongside headline metrics.

## Pilot result

Sprint 2 is complete. On eight adjudicated, scorable records, the DDOT inventory baseline
achieved 62.5 percent accuracy. The Project Sidewalk validator answered only one record,
for 12.5 percent coverage, so its answered-case accuracy is not treated as a performance
claim.

Sprint 3 is complete. A second blind pass produced five exact label agreements, six cases
where only one view set was scorable, and one direct conflict that received written
manual adjudication. The resolved set contains nine scorable records and three
`cannot_determine` records.

Target-centered framing raised Project Sidewalk model coverage from 11.1 percent to 77.8
percent on the resolved scorable set. Answered-case accuracy was 14.3 percent, with a 95
percent interval of 2.6 to 51.3 percent. Improved framing solved much of the view-eligibility
problem, while the pretrained validator still transferred poorly to this Mapillary pilot.

Sprint 4 is complete. Five inventory disagreements received historical-cause review.
All five remain unresolved because every available capture is newer than the 2016
inventory and no independent 2016 reference is present. The final QA split contains six
model errors, five unresolved inventory-history cases, and three records with insufficient
current imagery. None of the tested policies supports automated clearance.

See `outputs/sprint3_pilot_report.md`, `outputs/sprint4_adjudication_report.md`,
`outputs/sprint4_screening_costs.md`, `outputs/stakeholder_memo.md`, and
`outputs/sprint4_project_walkthrough.md`.

## Current scale-up status

Sprint 5 development preparation is complete. The scale-up split contains 72 development
records and 24 held-out records, with six development and two held-out records in every
area-by-condition stratum. All 12 pilot records are excluded. Coverage metadata exists for
both splits, while held-out thumbnails remain unopened.

The development batch contains 55 records with at least one target crop that passed the
frozen crop gate. The other 17 records remain in scope as evidence failures and receive
`cannot_determine` during labeling when no eligible evidence exists.

Remaining work:

1. Complete blind labels for all 72 development records.
2. Add a second reviewer and report agreement.
3. Train or select a model using imagery closer to the Mapillary deployment domain.
4. Freeze preprocessing and decision settings in a code revision.
5. Open held-out imagery and run the frozen policy once.

See `PROJECT_STATUS.md`, `outputs/sprint5_coverage_report.md`,
`outputs/sprint5_readiness_report.md`, and `outputs/project_summary.md` for the current
checkpoint.
