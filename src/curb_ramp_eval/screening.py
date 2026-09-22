from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path


TRUTH_LABELS = {"ramp_present", "ramp_absent", "cannot_determine"}
PREDICTION_LABELS = {"ramp_present", "ramp_absent", "abstain"}
INVENTORY_POPULATION = {
    "Good": 11_020,
    "Non-Compliant": 16_139,
    "Fair": 3_638,
    "Missing": 3_885,
}


def _read_csv(path: str | Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return [dict(row) for row in csv.DictReader(stream)]


def _require_fields(rows: list[dict], fields: set[str], name: str) -> None:
    if not rows:
        raise ValueError(f"{name} is empty")
    missing = fields - set(rows[0])
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")


def load_truth_labels(path: str | Path) -> list[dict]:
    rows = _read_csv(path)
    _require_fields(
        rows,
        {"record_id", "study_area", "inventory_condition", "truth_label"},
        "truth labels",
    )
    completed = [row for row in rows if row["truth_label"].strip()]
    if not completed:
        raise ValueError("truth labels has no completed truth_label values")
    seen: set[str] = set()
    for row in completed:
        record_id = row["record_id"].strip()
        if not record_id:
            raise ValueError("Every truth row needs a record_id")
        if record_id in seen:
            raise ValueError(f"Duplicate truth record_id: {record_id}")
        seen.add(record_id)
        if row["truth_label"] not in TRUTH_LABELS:
            raise ValueError(
                f"Invalid truth_label {row['truth_label']!r} for record {record_id}"
            )
    return completed


def load_screening_predictions(path: str | Path) -> list[dict]:
    rows = _read_csv(path)
    _require_fields(
        rows,
        {"record_id", "model_name", "predicted_label", "confidence"},
        "predictions",
    )
    model_names = {row["model_name"].strip() for row in rows}
    if "" in model_names:
        raise ValueError("Every prediction row needs a model_name")
    if len(model_names) != 1:
        raise ValueError(
            "A screening evaluation file must contain exactly one model; "
            f"found {sorted(model_names)}"
        )

    seen: set[str] = set()
    for row in rows:
        record_id = row["record_id"].strip()
        if not record_id:
            raise ValueError("Every prediction row needs a record_id")
        if record_id in seen:
            raise ValueError(f"Duplicate prediction record_id: {record_id}")
        seen.add(record_id)
        key = (row["model_name"], record_id)
        if row["predicted_label"] not in PREDICTION_LABELS:
            raise ValueError(
                f"Invalid predicted_label {row['predicted_label']!r} for {key}"
            )
        try:
            row["confidence"] = float(row["confidence"])
        except ValueError as exc:
            raise ValueError(f"Invalid confidence for {key}") from exc
        if not 0 <= row["confidence"] <= 1:
            raise ValueError(f"Confidence outside [0, 1] for {key}")
        if row.get("latency_ms"):
            row["latency_ms"] = float(row["latency_ms"])
    return rows


def inventory_baseline_predictions(truth_rows: list[dict]) -> list[dict]:
    predictions: list[dict] = []
    for row in truth_rows:
        condition = row["inventory_condition"]
        if condition not in INVENTORY_POPULATION:
            predicted_label = "abstain"
            confidence = 0.0
        else:
            predicted_label = "ramp_absent" if condition == "Missing" else "ramp_present"
            confidence = 1.0
        predictions.append(
            {
                "record_id": row["record_id"],
                "model_name": "ddot_2016_inventory_baseline",
                "predicted_label": predicted_label,
                "confidence": confidence,
                "latency_ms": 0.0,
                "quality_gate_pass": "",
                "image_ids": "",
            }
        )
    return predictions


def wilson_interval(successes: float, total: float, z: float = 1.96) -> dict:
    if total <= 0:
        return {"low": None, "high": None}
    rate = successes / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt((rate * (1 - rate) / total) + (z * z / (4 * total * total)))
        / denominator
    )
    return {"low": round(max(0.0, center - margin), 4), "high": round(min(1.0, center + margin), 4)}


def _safe_divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def _metric_bundle(tp: float, tn: float, fp: float, fn: float) -> dict:
    answered = tp + tn + fp + fn
    actual_positive = tp + fn
    predicted_positive = tp + fp
    precision = _safe_divide(tp, predicted_positive)
    recall = _safe_divide(tp, actual_positive)
    accuracy = _safe_divide(tp + tn, answered)
    f1 = None
    if precision is not None and recall is not None and precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "counts": {
            "true_positive": round(tp, 4),
            "true_negative": round(tn, 4),
            "false_positive": round(fp, 4),
            "false_negative": round(fn, 4),
            "answered": round(answered, 4),
        },
        "metrics": {
            "precision": round(precision, 4) if precision is not None else None,
            "recall": round(recall, 4) if recall is not None else None,
            "f1": round(f1, 4) if f1 is not None else None,
            "accuracy": round(accuracy, 4) if accuracy is not None else None,
        },
        "intervals_95": {
            "precision": wilson_interval(tp, predicted_positive),
            "recall": wilson_interval(tp, actual_positive),
            "accuracy": wilson_interval(tp + tn, answered),
        },
    }


def _confusion(rows: list[dict]) -> tuple[int, int, int, int]:
    tp = sum(row["truth_label"] == "ramp_present" and row["predicted_label"] == "ramp_present" for row in rows)
    tn = sum(row["truth_label"] == "ramp_absent" and row["predicted_label"] == "ramp_absent" for row in rows)
    fp = sum(row["truth_label"] == "ramp_absent" and row["predicted_label"] == "ramp_present" for row in rows)
    fn = sum(row["truth_label"] == "ramp_present" and row["predicted_label"] == "ramp_absent" for row in rows)
    return tp, tn, fp, fn


def _population_reweighted(per_condition_rows: dict[str, list[dict]]) -> dict:
    population_total = sum(INVENTORY_POPULATION.values())
    weighted = {"tp": 0.0, "tn": 0.0, "fp": 0.0, "fn": 0.0}
    included_weight = 0.0
    for condition, population_count in INVENTORY_POPULATION.items():
        rows = per_condition_rows.get(condition, [])
        if not rows:
            continue
        tp, tn, fp, fn = _confusion(rows)
        answered = tp + tn + fp + fn
        if not answered:
            continue
        weight = population_count / population_total
        included_weight += weight
        weighted["tp"] += weight * tp / answered
        weighted["tn"] += weight * tn / answered
        weighted["fp"] += weight * fp / answered
        weighted["fn"] += weight * fn / answered
    if not included_weight:
        return {"included_population_weight": 0.0, **_metric_bundle(0, 0, 0, 0)}
    normalized = {key: value / included_weight for key, value in weighted.items()}
    result = {
        "included_population_weight": round(included_weight, 4),
        **_metric_bundle(normalized["tp"], normalized["tn"], normalized["fp"], normalized["fn"]),
    }
    result["intervals_95"] = {
        "method": None,
        "note": "Not estimated for the pilot. Wilson intervals are not valid on normalized population-weighted pseudo-counts.",
    }
    return result


def evaluate_screening(
    truth_rows: list[dict],
    prediction_rows: list[dict],
    confidence_threshold: float = 0.70,
) -> dict:
    if not 0 <= confidence_threshold <= 1:
        raise ValueError("confidence_threshold must be between 0 and 1")
    if prediction_rows:
        model_names = {row["model_name"] for row in prediction_rows}
        if len(model_names) != 1:
            raise ValueError(
                "evaluate_screening expects predictions from exactly one model; "
                f"found {sorted(model_names)}"
            )
    truth_by_id = {row["record_id"]: row for row in truth_rows}
    prediction_by_id = {row["record_id"]: row for row in prediction_rows}

    joined: list[dict] = []
    review_queue: list[dict] = []
    for record_id, truth in truth_by_id.items():
        prediction = prediction_by_id.get(record_id)
        if prediction is None:
            prediction = {
                "record_id": record_id,
                "model_name": prediction_rows[0]["model_name"] if prediction_rows else "unknown",
                "predicted_label": "abstain",
                "confidence": 0.0,
                "latency_ms": "",
                "quality_gate_pass": "",
                "image_ids": "",
            }
        effective_prediction = prediction["predicted_label"]
        if prediction["confidence"] < confidence_threshold:
            effective_prediction = "abstain"
        row = {**truth, **prediction, "effective_prediction": effective_prediction}

        reasons: list[str] = []
        if truth["truth_label"] == "cannot_determine":
            reasons.append("imagery_insufficient")
        elif effective_prediction == "abstain":
            reasons.append("model_abstention")
        elif effective_prediction != truth["truth_label"]:
            reasons.append("model_error")
        if reasons:
            row["review_reasons"] = "|".join(reasons)
            review_queue.append(row)
        joined.append(row)

    scored_truth = [row for row in joined if row["truth_label"] != "cannot_determine"]
    answered = [row for row in scored_truth if row["effective_prediction"] != "abstain"]
    for row in answered:
        row["predicted_label"] = row["effective_prediction"]

    tp, tn, fp, fn = _confusion(answered)
    overall = _metric_bundle(tp, tn, fp, fn)
    overall["counts"].update(
        {
            "truth_records": len(joined),
            "scorable_truth_records": len(scored_truth),
            "cannot_determine": len(joined) - len(scored_truth),
            "abstained": len(scored_truth) - len(answered),
        }
    )
    overall["metrics"].update(
        {
            "coverage": round(len(answered) / len(scored_truth), 4) if scored_truth else None,
            "abstention_rate": round((len(scored_truth) - len(answered)) / len(scored_truth), 4) if scored_truth else None,
            "imagery_insufficient_rate": round((len(joined) - len(scored_truth)) / len(joined), 4) if joined else None,
        }
    )

    per_condition_source: dict[str, list[dict]] = defaultdict(list)
    for row in answered:
        per_condition_source[row["inventory_condition"]].append(row)
    per_condition = {
        condition: _metric_bundle(*_confusion(rows))
        for condition, rows in sorted(per_condition_source.items())
    }

    latencies = [
        float(row["latency_ms"])
        for row in prediction_rows
        if row.get("latency_ms") not in (None, "")
    ]
    return {
        "model_name": prediction_rows[0]["model_name"] if prediction_rows else "unknown",
        "confidence_threshold": confidence_threshold,
        "overall": overall,
        "per_inventory_condition": per_condition,
        "population_reweighted": _population_reweighted(per_condition_source),
        "latency_ms": {
            "count": len(latencies),
            "mean": round(sum(latencies) / len(latencies), 3) if latencies else None,
        },
        "joined_rows": joined,
        "review_queue": review_queue,
    }
