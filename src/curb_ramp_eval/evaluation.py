from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


EARTH_RADIUS_METERS = 6_371_008.8


@dataclass(frozen=True)
class EvaluationConfig:
    match_radius_meters: float = 12.0
    confidence_threshold: float = 0.70


def _parse_binary(value: str, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be 0 or 1; received {value!r}") from exc
    if parsed not in (0, 1):
        raise ValueError(f"{field_name} must be 0 or 1; received {value!r}")
    return parsed


def _parse_coordinate(value: str, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric; received {value!r}") from exc


def load_ground_truth(path: str | Path) -> list[dict]:
    required = {
        "record_id",
        "latitude",
        "longitude",
        "ramp_present",
        "condition",
        "source",
    }
    rows = _load_csv(path, required)
    for row in rows:
        row["latitude"] = _parse_coordinate(row["latitude"], "latitude")
        row["longitude"] = _parse_coordinate(row["longitude"], "longitude")
        row["ramp_present"] = _parse_binary(row["ramp_present"], "ramp_present")
    return rows


def load_predictions(path: str | Path) -> list[dict]:
    required = {
        "prediction_id",
        "latitude",
        "longitude",
        "ramp_present",
        "confidence",
        "condition",
        "image_id",
        "model_name",
    }
    rows = _load_csv(path, required)
    for row in rows:
        row["latitude"] = _parse_coordinate(row["latitude"], "latitude")
        row["longitude"] = _parse_coordinate(row["longitude"], "longitude")
        row["ramp_present"] = _parse_binary(row["ramp_present"], "ramp_present")
        row["confidence"] = _parse_coordinate(row["confidence"], "confidence")
        if not 0 <= row["confidence"] <= 1:
            raise ValueError("confidence must be between 0 and 1")
    return rows


def _load_csv(path: str | Path, required: set[str]) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        missing = required - fields
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        return [dict(row) for row in reader]


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * math.asin(math.sqrt(a))


def match_records(
    ground_truth: Iterable[dict],
    predictions: Iterable[dict],
    radius_meters: float,
) -> tuple[list[dict], list[dict], list[dict]]:
    truths = list(ground_truth)
    available_truth_indices = set(range(len(truths)))
    matches: list[dict] = []
    unmatched_predictions: list[dict] = []

    for prediction in sorted(predictions, key=lambda row: row["confidence"], reverse=True):
        candidates: list[tuple[float, int]] = []
        for index in available_truth_indices:
            truth = truths[index]
            distance = haversine_meters(
                prediction["latitude"],
                prediction["longitude"],
                truth["latitude"],
                truth["longitude"],
            )
            if distance <= radius_meters:
                candidates.append((distance, index))

        if not candidates:
            unmatched_predictions.append(prediction)
            continue

        distance, truth_index = min(candidates)
        available_truth_indices.remove(truth_index)
        matches.append(
            {
                **truths[truth_index],
                **{f"pred_{key}": value for key, value in prediction.items()},
                "distance_meters": round(distance, 3),
            }
        )

    unmatched_truths = [truths[index] for index in sorted(available_truth_indices)]
    return matches, unmatched_predictions, unmatched_truths


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate_records(
    ground_truth: list[dict],
    predictions: list[dict],
    config: EvaluationConfig | None = None,
) -> dict:
    config = config or EvaluationConfig()
    matches, unmatched_predictions, unmatched_truths = match_records(
        ground_truth,
        predictions,
        config.match_radius_meters,
    )

    scored = [
        row
        for row in matches
        if row["pred_confidence"] >= config.confidence_threshold
    ]
    abstained = [
        row
        for row in matches
        if row["pred_confidence"] < config.confidence_threshold
    ]

    tp = sum(row["ramp_present"] == 1 and row["pred_ramp_present"] == 1 for row in scored)
    tn = sum(row["ramp_present"] == 0 and row["pred_ramp_present"] == 0 for row in scored)
    fp = sum(row["ramp_present"] == 0 and row["pred_ramp_present"] == 1 for row in scored)
    fn = sum(row["ramp_present"] == 1 and row["pred_ramp_present"] == 0 for row in scored)

    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    accuracy = _safe_divide(tp + tn, len(scored))

    review_queue: list[dict] = []
    for row in matches:
        reasons = []
        if row["pred_confidence"] < config.confidence_threshold:
            reasons.append("low_confidence")
        if row["ramp_present"] != row["pred_ramp_present"]:
            reasons.append("inventory_model_disagreement")
        if row["condition"] and row["pred_condition"]:
            if row["condition"].strip().lower() != row["pred_condition"].strip().lower():
                reasons.append("condition_disagreement")
        if reasons:
            review_queue.append({**row, "review_reasons": "|".join(reasons)})

    for row in unmatched_predictions:
        review_queue.append(
            {
                **{f"pred_{key}": value for key, value in row.items()},
                "review_reasons": "unmatched_prediction",
            }
        )
    for row in unmatched_truths:
        review_queue.append({**row, "review_reasons": "unmatched_inventory_record"})

    metrics = {
        "config": asdict(config),
        "counts": {
            "ground_truth_records": len(ground_truth),
            "predictions": len(predictions),
            "matched_records": len(matches),
            "scored_records": len(scored),
            "abstained_records": len(abstained),
            "review_queue_records": len(review_queue),
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
        },
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "accuracy": round(accuracy, 4),
            "coverage": round(_safe_divide(len(scored), len(matches)), 4),
            "match_rate": round(_safe_divide(len(matches), len(ground_truth)), 4),
        },
    }

    return {
        "metrics": metrics,
        "matches": matches,
        "review_queue": review_queue,
        "unmatched_predictions": unmatched_predictions,
        "unmatched_truths": unmatched_truths,
    }


def write_json(data: dict, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)


def write_csv(rows: list[dict], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output.write_text("", encoding="utf-8")
        return
    fields = sorted({field for row in rows for field in row})
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
