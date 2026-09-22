# Model provenance and evaluation caveats

## Core local model

- Model: `projectsidewalk/quantized_curb_ramp_dinov2_tiny_onnx`
- Publisher: Project Sidewalk
- License shown by the publisher: MIT
- Pinned revision: `a9da393f2b41d72f5252ba9e50291168bdcfd668`
- ONNX SHA256: `35405fe96dd815298923d8f008842915c30265e1247a285a7d680c2c0fb20cb1`
- Source: <https://huggingface.co/projectsidewalk/quantized_curb_ramp_dinov2_tiny_onnx>
- Architecture: quantized DINOv2 image classifier
- Published label mapping: class 0 `correct`, class 1 `incorrect`
- Published preprocessing: resize shortest edge to 256, center crop to 224 by 224,
  rescale to [0, 1], then ImageNet mean and standard-deviation normalization.

The published class-0 score is stored as `validator_correct_probability`. It is the
model's probability for its published `correct` class, not a calibrated probability that
a curb ramp is physically present. AccessLens experimentally maps that score to
present/absent/abstain decisions under frozen thresholds so cross-source transfer can be
measured. Older cached pilot image-prediction files used the field name
`curb_ramp_probability`; the code can still read that legacy name for reproducibility.

The model checks whether a centered candidate curb-ramp crop is a correct label. In this
project, a selected directional Mapillary image is eligible only when the camera location
is close to the inventory point and its heading is aligned with that point. The remaining
cross-source and crop-construction shift is measured as part of the evaluation.

## Why RampNet is a stretch arm

RampNet is Project Sidewalk's full-panorama curb-ramp detector:
<https://github.com/ProjectSidewalk/RampNet>. Its published quick-start recipe resizes an
equirectangular panorama to 4096 by 2048 and returns heatmap peaks. That is a different
task from validating a centered candidate crop.

The repository also documents a July 2026 evaluation correction: detections must be
matched one-to-one with ground truth, and redundant detections count as false positives.
AccessLens uses one-to-one geographic matching in its legacy detector harness and scores
the validator at the inventory-record level.

## Interpretation

An out-of-domain failure is a project finding. Model scores are never used as proof of
ADA or PROWAG compliance. Thresholds are selected on a development subset, frozen, and
then reported on held-out records.
