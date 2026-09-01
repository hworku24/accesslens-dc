from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.evaluation import write_csv, write_json  # noqa: E402
from curb_ramp_eval.screening import (  # noqa: E402
    evaluate_screening,
    load_screening_predictions,
    load_truth_labels,
)


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "model"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a record-level curb-ramp screening model")
    parser.add_argument("predictions", type=Path)
    parser.add_argument(
        "--labels",
        type=Path,
        default=ROOT / "data/labels/curb_ramp_labels.csv",
    )
    parser.add_argument("--confidence-threshold", type=float, default=0.70)
    args = parser.parse_args()

    truth = load_truth_labels(args.labels)
    predictions = load_screening_predictions(args.predictions)
    result = evaluate_screening(truth, predictions, args.confidence_threshold)
    output_dir = ROOT / "outputs" / safe_slug(result["model_name"])
    report = {
        key: value
        for key, value in result.items()
        if key not in {"joined_rows", "review_queue"}
    }
    write_json(report, output_dir / "metrics.json")
    write_csv(result["joined_rows"], output_dir / "scored_records.csv")
    write_csv(result["review_queue"], output_dir / "review_queue.csv")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
