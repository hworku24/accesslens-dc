from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.evaluation import write_csv, write_json  # noqa: E402
from curb_ramp_eval.screening import (  # noqa: E402
    evaluate_screening,
    inventory_baseline_predictions,
    load_truth_labels,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Score the DDOT 2016 inventory baseline")
    parser.add_argument(
        "--labels",
        type=Path,
        default=ROOT / "data/labels/curb_ramp_labels.csv",
    )
    parser.add_argument("--confidence-threshold", type=float, default=0.70)
    args = parser.parse_args()

    truth = load_truth_labels(args.labels)
    predictions = inventory_baseline_predictions(truth)
    result = evaluate_screening(truth, predictions, args.confidence_threshold)

    output_dir = ROOT / "outputs/inventory_baseline"
    report = {key: value for key, value in result.items() if key not in {"joined_rows", "review_queue"}}
    write_json(report, output_dir / "metrics.json")
    write_csv(predictions, output_dir / "predictions.csv")
    write_csv(result["joined_rows"], output_dir / "scored_records.csv")
    write_csv(result["review_queue"], output_dir / "review_queue.csv")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

