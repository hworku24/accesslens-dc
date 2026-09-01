from __future__ import annotations

import collections
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InventoryAudit:
    path: str
    source_url: str
    sha256: str
    audited_at_utc: str
    feature_count: int
    geometry_type_counts: dict[str, int]
    coordinate_dimensions: dict[str, int]
    bounds_wgs84: dict[str, float]
    condition_counts: dict[str, int]
    year_inspected_counts: dict[str, int]
    status_counts: dict[str, int]
    null_counts: dict[str, int]
    duplicate_non_null_counts: dict[str, int]
    distinct_non_null_counts: dict[str, int]
    estimated_improvement_year_counts: dict[str, int]
    last_edited_date_counts: dict[str, int]


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_feature_collection(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection":
        raise ValueError("Expected a GeoJSON FeatureCollection")
    if not isinstance(data.get("features"), list):
        raise ValueError("GeoJSON is missing a feature list")
    return data


def _display(value: Any) -> str:
    return "<null>" if value is None or value == "" else str(value)


def _counts(values: list[Any]) -> dict[str, int]:
    counter = collections.Counter(_display(value) for value in values)
    return dict(sorted(counter.items(), key=lambda pair: (-pair[1], pair[0])))


def audit_inventory(path: str | Path, source_url: str = "") -> InventoryAudit:
    source = Path(path)
    data = load_feature_collection(source)
    features = data["features"]

    properties = [feature.get("properties") or {} for feature in features]
    fields = sorted({field for row in properties for field in row})

    geometry_types = _counts(
        [(feature.get("geometry") or {}).get("type") for feature in features]
    )
    coordinates = [
        (feature.get("geometry") or {}).get("coordinates")
        for feature in features
    ]
    usable_coordinates = [
        value
        for value in coordinates
        if isinstance(value, list) and len(value) >= 2
    ]
    dimensions = _counts([len(value) for value in usable_coordinates])

    if not usable_coordinates:
        raise ValueError("No usable point coordinates were found")

    null_counts: dict[str, int] = {}
    duplicate_counts: dict[str, int] = {}
    distinct_counts: dict[str, int] = {}
    for field in fields:
        values = [row.get(field) for row in properties]
        non_null = [value for value in values if value is not None and value != ""]
        null_counts[field] = len(values) - len(non_null)
        distinct_counts[field] = len(set(non_null))
        duplicate_counts[field] = len(non_null) - len(set(non_null))

    return InventoryAudit(
        path=str(source),
        source_url=source_url,
        sha256=sha256_file(source),
        audited_at_utc=datetime.now(timezone.utc).isoformat(),
        feature_count=len(features),
        geometry_type_counts=geometry_types,
        coordinate_dimensions=dimensions,
        bounds_wgs84={
            "min_longitude": min(value[0] for value in usable_coordinates),
            "min_latitude": min(value[1] for value in usable_coordinates),
            "max_longitude": max(value[0] for value in usable_coordinates),
            "max_latitude": max(value[1] for value in usable_coordinates),
        },
        condition_counts=_counts([row.get("CONDITION") for row in properties]),
        year_inspected_counts=_counts([row.get("YEAR_INSPECTED") for row in properties]),
        status_counts=_counts([row.get("STATUS") for row in properties]),
        null_counts=null_counts,
        duplicate_non_null_counts=duplicate_counts,
        distinct_non_null_counts=distinct_counts,
        estimated_improvement_year_counts=_counts(
            [row.get("ESTIMATED_YEAR_OF_IMPROVEMENT") for row in properties]
        ),
        last_edited_date_counts=_counts(
            [row.get("LAST_EDITED_DATE") for row in properties]
        ),
    )


def write_audit_json(audit: InventoryAudit, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(asdict(audit), indent=2), encoding="utf-8")


def audit_to_markdown(audit: InventoryAudit) -> str:
    lines = [
        "# DDOT ADA curb-ramp inventory audit",
        "",
        f"Audit timestamp: `{audit.audited_at_utc}`  ",
        f"Source file: `{audit.path}`  ",
        f"Source URL: <{audit.source_url}>  " if audit.source_url else "Source URL: not recorded  ",
        f"SHA256: `{audit.sha256}`",
        "",
        "## Headline findings",
        "",
        f"- Feature count: {audit.feature_count:,}",
        f"- Geometry types: {audit.geometry_type_counts}",
        f"- Coordinate dimensions: {audit.coordinate_dimensions}",
        f"- Inspection years: {audit.year_inspected_counts}",
        f"- Conditions: {audit.condition_counts}",
        f"- Status codes: {audit.status_counts}",
        "",
        "## Field-quality findings",
        "",
        f"- `GIS_ID` nulls: {audit.null_counts.get('GIS_ID', 0):,}",
        f"- `GIS_ID` duplicate non-null values: {audit.duplicate_non_null_counts.get('GIS_ID', 0):,}",
        f"- `INTERSECTION_ID` nulls: {audit.null_counts.get('INTERSECTION_ID', 0):,}",
        "- `INTERSECTION_ID` cannot support intersection grouping in this download.",
        f"- Estimated improvement years: {audit.estimated_improvement_year_counts}",
        "- The improvement-year field has one value across the dataset and cannot verify individual construction dates.",
        f"- Last-edited dates: {audit.last_edited_date_counts}",
        "- A file edit date does not establish a new field inspection date.",
        "- `STATUS` is retained as an undocumented code and excluded from semantic claims.",
        "",
        "## Bounds",
        "",
        f"```json\n{json.dumps(audit.bounds_wgs84, indent=2)}\n```",
        "",
        "## Interpretation",
        "",
        "All records report a 2016 inspection year. The dataset is suitable as a historical inventory baseline. Current presence and condition must be established from newer evidence. The project will score the inventory as one predictor against hand-labeled current imagery.",
        "",
    ]
    return "\n".join(lines)
