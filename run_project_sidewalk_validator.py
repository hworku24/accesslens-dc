from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.evaluation import write_csv  # noqa: E402
from curb_ramp_eval.image_quality import classify_quality, inspect_image, load_thresholds  # noqa: E402
from curb_ramp_eval.validator import (  # noqa: E402
    OnnxCurbRampValidator,
    aggregate_all_records,
)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Project Sidewalk ONNX validator")
    parser.add_argument(
        "--manifest-file",
        type=Path,
        default=ROOT / "data/processed/mapillary_image_manifest.csv",
    )
    parser.add_argument(
        "--candidate-file",
        type=Path,
        default=ROOT / "data/processed/mapillary_coverage_candidates.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs/project_sidewalk_validator",
    )
    parser.add_argument(
        "--quality-thresholds",
        type=Path,
        default=ROOT / "config/image_quality_thresholds.json",
    )
    parser.add_argument("--model-name", default=None)
    args = parser.parse_args()
    manifest_path = args.manifest_file if args.manifest_file.is_absolute() else ROOT / args.manifest_file
    candidate_path = args.candidate_file if args.candidate_file.is_absolute() else ROOT / args.candidate_file
    manifest = read_csv(manifest_path)
    candidates = read_csv(candidate_path)
    quality_path = (
        args.quality_thresholds
        if args.quality_thresholds.is_absolute()
        else ROOT / args.quality_thresholds
    )
    quality_thresholds = load_thresholds(quality_path)
    validator_thresholds = json.loads(
        (ROOT / "config/validator_thresholds.json").read_text(encoding="utf-8")
    )
    model_path = (
        ROOT
        / "weights/projectsidewalk/quantized_curb_ramp_dinov2_tiny_onnx/model_quantized.onnx"
    )
    if not model_path.exists():
        raise FileNotFoundError("Run download_project_sidewalk_model.py first")
    model = OnnxCurbRampValidator(model_path)

    image_results: list[dict] = []
    for index, row in enumerate(manifest, start=1):
        path = ROOT / row["image_path"]
        metrics = inspect_image(path)
        quality = classify_quality(metrics, quality_thresholds)
        heading = float(row["heading_difference_deg"]) if row["heading_difference_deg"] else 999.0
        distance = float(row["distance_to_record_m"])
        rejection_reasons: list[str] = []
        if not quality["quality_gate_pass"]:
            rejection_reasons.append("image_quality")
        if str(row["is_pano"]).lower() in {"true", "1"}:
            rejection_reasons.append("panorama_requires_directional_projection")
        if heading > validator_thresholds["maximum_heading_difference_degrees"]:
            rejection_reasons.append("target_not_centered")
        if distance > validator_thresholds["maximum_camera_distance_meters"]:
            rejection_reasons.append("camera_too_far")

        result = {
            **row,
            **metrics,
            **quality,
            "inference_status": "rejected" if rejection_reasons else "scored",
            "inference_rejection_reasons": "|".join(rejection_reasons),
        }
        if not rejection_reasons:
            result.update(model.predict(path))
        image_results.append(result)
        print(f"[{index}/{len(manifest)}] {row['image_id']}: {result['inference_status']}")

    predictions = aggregate_all_records(candidates, image_results, validator_thresholds)
    if args.model_name:
        for prediction in predictions:
            prediction["model_name"] = args.model_name
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    write_csv(image_results, output / "image_predictions.csv")
    write_csv(predictions, output / "predictions.csv")
    print(f"Wrote {len(predictions)} record predictions to {output}")


if __name__ == "__main__":
    main()
