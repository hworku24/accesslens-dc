from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.evaluation import (  # noqa: E402
    EvaluationConfig,
    evaluate_records,
    load_ground_truth,
    load_predictions,
    write_csv,
    write_json,
)


def main() -> None:
    ground_truth = load_ground_truth(ROOT / "data/sample/ground_truth.csv")
    predictions = load_predictions(ROOT / "data/sample/predictions.csv")
    result = evaluate_records(
        ground_truth,
        predictions,
        EvaluationConfig(match_radius_meters=12, confidence_threshold=0.70),
    )

    outputs = ROOT / "outputs"
    write_json(result["metrics"], outputs / "evaluation_metrics.json")
    write_csv(result["review_queue"], outputs / "review_queue.csv")
    write_csv(result["matches"], outputs / "matched_records.csv")

    print("AccessLens DC legacy matching demo")
    print("==================================")
    for name, value in result["metrics"]["metrics"].items():
        print(f"{name:>12}: {value:.4f}")
    print(f"review queue: {len(result['review_queue'])} records")
    print(f"outputs: {outputs}")


if __name__ == "__main__":
    main()
