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
- Three defined DC study areas and 144 seeded, stratified candidates.
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

See `data_notes.md` for counts, bounds, nulls, duplicate checks, timestamps, and the
source-file hash.

## Repository layout

```text
accesslens-dc/
├── config/                    Frozen and provisional policy settings
├── data/
│   ├── labels/                Protected human-label sheet
│   ├── processed/             Audits, samples, and imagery manifests
│   └── raw/                   Pinned DDOT source download
├── docs/                      Domain, architecture, labeling, and model notes
├── outputs/                   Maps, metrics, predictions, and review queues
├── src/curb_ramp_eval/        Reusable project code
├── tests/                     Automated verification
└── eval_protocol.md           Evaluation policy frozen before model results
```

## Reproduce the completed foundation

```bash
python3 audit_inventory.py
python3 make_coverage_sample.py
python3 make_candidate_map.py
python3 -m unittest discover -s tests -v
```

Open `outputs/candidate_map.html` to inspect the real sampled locations.

## Continue with Mapillary

Create a free Mapillary developer token and keep it in your local shell:

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
by version control.

Start with 12 points. Review coverage and view relevance before collecting the full
sample. The access token is read from the environment and is excluded from version
control.

## Run the local model

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python download_project_sidewalk_model.py
.venv/bin/python audit_image_quality.py
.venv/bin/python run_project_sidewalk_validator.py
```

The model revision and downloaded file hashes are stored under the ignored `weights/`
directory. Model and quality thresholds remain marked provisional until a small
development subset has been reviewed.

## Label and evaluate

Follow `docs/labeling-guide.md`. Complete at least 50 usable locations, retain every
`cannot_determine` case, and relabel 25 records after a break.

After the label sheet is complete:

```bash
.venv/bin/python run_inventory_baseline.py
.venv/bin/python run_screening_evaluation.py \
  outputs/project_sidewalk_validator/predictions.csv
```

The baseline maps `Missing` to `ramp_absent` and Good, Fair, or Non-Compliant to
`ramp_present`. It is scored against current human-reviewed imagery, so disagreements
remain candidates for investigation, not claims that the inventory is wrong.

## Evidence standard

The frozen protocol, source hashes, model revision, raw per-image scores, abstentions,
and disagreement records are retained. A strong result includes the failures and the
coverage limitations alongside the headline metric.

## Pilot result

Sprint 2 is complete. On eight adjudicated, scorable records, the DDOT inventory baseline
achieved 62.5 percent accuracy. The Project Sidewalk validator answered only one record,
for 12.5 percent coverage, so its answered-case accuracy is not treated as a performance
claim. See `outputs/sprint2_pilot_report.md` and `outputs/pilot_adjudication.csv`.

Sprint 3 is complete. A second blind pass produced five exact label agreements, six cases
where only one view set was scorable, and one direct conflict that received written
manual adjudication. The resolved set contains nine scorable records and three
cannot-determine records.

Target-centered framing raised Project Sidewalk model coverage from 11.1 percent to 77.8
percent on the resolved scorable set. Answered-case accuracy was 14.3 percent, with a 95
percent interval of 2.6 to 51.3 percent. The result indicates poor transfer from the
model's published validation task to this Mapillary pilot.

See `outputs/sprint3_pilot_report.md`, `outputs/stakeholder_memo.md`, and
`outputs/pilot_result_map.html`.

Sprint 4 is complete. Five inventory disagreements received historical-cause review.
All five remain unresolved because every available capture is newer than the 2016
inventory and no independent 2016 reference is present. The final QA split contains six
model errors, five unresolved inventory-history cases, and three records with insufficient
current imagery.

The field-review analysis treats absent ramps as the review target and routes abstentions
to review. The source-view model avoided missed absent ramps by sending every scorable
record to the field. The inventory baseline and target-centered model each missed five of
seven absent ramps. None of the tested policies supports automated clearance.

See `outputs/sprint4_adjudication_report.md`, `outputs/sprint4_screening_costs.md`,
`outputs/stakeholder_memo.md`, and `outputs/sprint4_project_walkthrough.md`.

Sprint 5 development preparation is complete. The scale-up split contains 72 development
records and 24 held-out records, with six development and two held-out records in every
area-by-condition stratum. All 12 pilot records are excluded. Coverage metadata exists for
both splits, while held-out thumbnails remain unopened.

The development batch contains 55 records with at least one target crop that passed the
frozen crop gate. The other 17 records remain in scope as evidence failures. Complete the
blind review at `outputs/scaleup_development_labeling_app.html` through the local server.

Rebuild the development labeling artifact with:

```bash
.venv/bin/python make_pilot_labeling_app.py \
  --candidate-file data/processed/mapillary_scaleup_development_candidates.csv \
  --manifest-file data/processed/mapillary_scaleup_development_target_crop_quality.csv \
  --output-file outputs/scaleup_development_labeling_app.html \
  --storage-key accesslens-scaleup-development-labels-v1 \
  --export-filename accesslens_scaleup_development_labels.csv \
  --quality-passed-only
```

See `outputs/sprint5_coverage_report.md` and `outputs/sprint5_readiness_report.md` for
coverage, evidence failures, and the held-out separation rule.

After exporting all 12 target-crop labels, finish reconciliation and scoring with:

```bash
.venv/bin/python finish_sprint3.py /path/to/accesslens_target_crop_labels.csv
```

Direct present-versus-absent conflicts produce a manual adjudication template. Each
conflict requires a final label and written reason before the script writes final metrics.

Regenerate the Sprint 4 QA outputs with:

```bash
.venv/bin/python make_inventory_adjudication_app.py
.venv/bin/python finish_sprint4.py
.venv/bin/python build_sprint4_analysis.py
```
