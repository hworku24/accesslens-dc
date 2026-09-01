from __future__ import annotations

import csv
import json
import random
from pathlib import Path


ELIGIBLE_CONDITIONS = ("Good", "Non-Compliant", "Fair", "Missing")


def load_study_areas(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for name, area in data.items():
        bbox = area.get("bbox_wgs84")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise ValueError(f"Study area {name!r} must contain a four-value bbox")
        min_lon, min_lat, max_lon, max_lat = bbox
        if min_lon >= max_lon or min_lat >= max_lat:
            raise ValueError(f"Study area {name!r} has an invalid bbox")
    return data


def point_in_bbox(longitude: float, latitude: float, bbox: list[float]) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= longitude <= max_lon and min_lat <= latitude <= max_lat


def inventory_rows(geojson_path: str | Path) -> list[dict]:
    data = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    rows: list[dict] = []
    for feature in data["features"]:
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        properties = feature.get("properties") or {}
        if geometry.get("type") != "Point" or len(coordinates) < 2:
            continue
        rows.append(
            {
                "record_id": properties.get("GIS_ID"),
                "object_id": properties.get("OBJECTID"),
                "longitude": float(coordinates[0]),
                "latitude": float(coordinates[1]),
                "elevation": coordinates[2] if len(coordinates) >= 3 else None,
                "condition": properties.get("CONDITION"),
                "year_inspected": properties.get("YEAR_INSPECTED"),
                "status_code": properties.get("STATUS"),
            }
        )
    return rows


def sample_coverage_candidates(
    rows: list[dict],
    study_areas: dict,
    per_condition_per_area: int = 12,
    seed: int = 20260901,
) -> list[dict]:
    rng = random.Random(seed)
    output: list[dict] = []
    for area_name, area in study_areas.items():
        bbox = area["bbox_wgs84"]
        area_rows = [
            row
            for row in rows
            if row["condition"] in ELIGIBLE_CONDITIONS
            and point_in_bbox(row["longitude"], row["latitude"], bbox)
        ]
        for condition in ELIGIBLE_CONDITIONS:
            candidates = [row for row in area_rows if row["condition"] == condition]
            rng.shuffle(candidates)
            selected = candidates[:per_condition_per_area]
            for row in selected:
                output.append({**row, "study_area": area_name})
    return sorted(output, key=lambda row: (row["study_area"], row["condition"], row["record_id"]))


def write_rows(rows: list[dict], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Cannot write an empty sample")
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sample_one_per_stratum(rows: list[dict], seed: int = 20260901) -> list[dict]:
    rng = random.Random(seed)
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        key = (row["study_area"], row["condition"])
        grouped.setdefault(key, []).append(row)
    selected: list[dict] = []
    for key in sorted(grouped):
        candidates = sorted(grouped[key], key=lambda row: row["record_id"])
        selected.append(rng.choice(candidates))
    return sorted(selected, key=lambda row: (row["study_area"], row["condition"]))
