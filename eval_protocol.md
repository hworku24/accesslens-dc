# AccessLens DC evaluation protocol

Version: 1.0  
Frozen: 2026-09-01  
Random seed: 20260901

## Research question

Can current, licensed street-level imagery and a pretrained curb-ramp model identify
which records in DDOT's 2016 ADA curb-ramp inventory warrant human review?

## Product boundary

The system screens inventory records for review. It does not issue an ADA or PROWAG
compliance determination.

Suitable image-based claims:

- a curb ramp appears present;
- a curb ramp appears absent;
- imagery is insufficient to decide;
- a detectable-warning surface appears visible;
- imagery and an inventory record appear to disagree.

Claims reserved for LiDAR, calibrated measurement, or field inspection:

- exact running slope or cross slope;
- exact width or grade-break geometry;
- tactile-warning dimensions and spacing;
- drainage and surface tolerances;
- formal legal compliance.

## Data sources

### DDOT inventory

- Source: DC Open Data, ADA Curb Ramp layer.
- Source assessment year: 2016.
- CRS on download: OGC CRS84 longitude and latitude.
- Meter-based calculations use EPSG:32618.
- The download date and SHA256 hash are recorded in `data_notes.md`.

### Street imagery

- Source: Mapillary API.
- Google Street View pixels are excluded.
- Image identifier, capture date, coordinates, camera type, and attribution are stored.
- Temporary signed URLs are never treated as durable provenance.

## Unit of analysis

The primary unit is a DDOT inventory point. Each point receives one final truth label
from one or two image crops.

Truth labels:

- `ramp_present`
- `ramp_absent`
- `cannot_determine`

If any usable crop clearly shows a ramp, the point is `ramp_present`. If all crops are
insufficient, the point is `cannot_determine`. Otherwise the point is `ramp_absent`.

## Sampling

The initial target is 120 inventory points:

- 40 Good
- 30 Non-Compliant
- 20 Fair
- 20 Missing
- 10 records held for a coverage-driven adjustment

The study includes two areas when Mapillary coverage permits:

- Navy Yard or Capitol Riverfront;
- one residential or east-of-river area.

The sample is seeded and stratified. Coverage-driven selection bias is reported.

## Labeling

Every usable crop is labeled before model inference. The labeling form records:

- truth label;
- image quality;
- occlusion;
- detectable-warning visibility;
- notes.

Twenty-five images are relabeled after a break. Raw self-agreement and resolved labels
are retained. Single-rater labeling is reported as a limitation.

## Model arms

Committed:

1. DDOT 2016 inventory as a baseline predictor. `Missing` maps to `ramp_absent`;
   Good, Fair, and Non-Compliant map to `ramp_present`.
2. Project Sidewalk local curb-ramp validator, using the published input recipe.
3. The local validator after OpenCV image-quality rejection.

Optional after the core evaluation works:

- a transfer-learned local classifier;
- a local or paid vision-language model;
- a detection model on a provenance-checked dataset.

## Image-quality gate

The OpenCV gate records blur, mean brightness, contrast, resolution, and crop validity.
Thresholds are frozen after inspecting a small development set. Rejected images are
reported as abstentions, not incorrect predictions.

## Metrics

Primary metrics:

- precision, recall, and F1;
- confusion matrix;
- accuracy on answered cases;
- abstention rate;
- imagery-insufficient rate;
- inference latency;
- 95 percent confidence intervals.

Records labeled `cannot_determine` are excluded from classification precision, recall,
and F1. Their count and share are reported separately.

Metrics are reported for each inventory condition. Population-reweighted results use
the observed DDOT condition distribution.

## Disagreement review

Every model-versus-truth and inventory-versus-truth disagreement receives one primary
code:

- `model_error`
- `possible_world_change`
- `possible_inventory_error`
- `imagery_insufficient`
- `ambiguous_geometry`

World-change and inventory-error findings remain qualified unless supported by an
independent source. Image capture date is retained as evidence.

## Success criteria

The MVP succeeds when it produces:

- a pinned and audited DDOT dataset;
- at least 50 hand-labeled usable DC locations;
- reproducible metrics with intervals;
- an image-quality abstention policy;
- a complete disagreement table;
- a review queue and local map;
- a concise recommendation on deployment.

