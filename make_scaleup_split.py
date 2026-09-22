from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "data/processed/mapillary_coverage_candidates.csv"
PILOT = ROOT / "data/processed/mapillary_pilot_candidates.csv"
DEVELOPMENT = ROOT / "data/processed/mapillary_scaleup_development_candidates.csv"
HELD_OUT = ROOT / "data/processed/mapillary_scaleup_heldout_candidates.csv"
MANIFEST = ROOT / "data/processed/mapillary_scaleup_split_manifest.json"
SEED = 20260922
DEVELOPMENT_PER_STRATUM = 6
HELD_OUT_PER_STRATUM = 2


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_split(
    candidates: list[dict],
    pilot_ids: set[str],
    seed: int = SEED,
    development_per_stratum: int = DEVELOPMENT_PER_STRATUM,
    held_out_per_stratum: int = HELD_OUT_PER_STRATUM,
) -> tuple[list[dict], list[dict]]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in candidates:
        if row["record_id"] not in pilot_ids:
            grouped[(row["study_area"], row["condition"])].append(dict(row))

    development = []
    held_out = []
    for stratum_index, key in enumerate(sorted(grouped)):
        rows = sorted(grouped[key], key=lambda row: row["record_id"])
        required = development_per_stratum + held_out_per_stratum
        if len(rows) < required:
            raise ValueError(f"Stratum {key} has {len(rows)} records; requires {required}")
        rng = random.Random(seed + stratum_index)
        rng.shuffle(rows)
        for order, row in enumerate(rows[:development_per_stratum], start=1):
            development.append(
                {**row, "split": "development", "selection_order": order, "split_seed": seed}
            )
        for order, row in enumerate(
            rows[development_per_stratum:required], start=1
        ):
            held_out.append(
                {**row, "split": "held_out", "selection_order": order, "split_seed": seed}
            )

    key_function = lambda row: (row["study_area"], row["condition"], int(row["selection_order"]))
    return sorted(development, key=key_function), sorted(held_out, key=key_function)


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def count_strata(rows: list[dict]) -> dict[str, int]:
    counts = Counter(f"{row['study_area']}::{row['condition']}" for row in rows)
    return dict(sorted(counts.items()))


def main() -> None:
    candidates = read_csv(CANDIDATES)
    pilot_ids = {row["record_id"] for row in read_csv(PILOT)}
    development, held_out = make_split(candidates, pilot_ids)
    write_csv(development, DEVELOPMENT)
    write_csv(held_out, HELD_OUT)
    manifest = {
        "created_date": "2026-09-22",
        "seed": SEED,
        "source_candidates": str(CANDIDATES.relative_to(ROOT)),
        "source_candidates_sha256": sha256(CANDIDATES),
        "pilot_exclusion_file": str(PILOT.relative_to(ROOT)),
        "pilot_exclusion_sha256": sha256(PILOT),
        "excluded_pilot_records": len(pilot_ids),
        "development_records": len(development),
        "held_out_records": len(held_out),
        "development_per_stratum": DEVELOPMENT_PER_STRATUM,
        "held_out_per_stratum": HELD_OUT_PER_STRATUM,
        "development_strata": count_strata(development),
        "held_out_strata": count_strata(held_out),
        "development_file_sha256": sha256(DEVELOPMENT),
        "held_out_file_sha256": sha256(HELD_OUT),
        "held_out_status": "sealed_for_preprocessing_and_threshold_work",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(development)} development records to {DEVELOPMENT}")
    print(f"Wrote {len(held_out)} held-out records to {HELD_OUT}")
    print(f"Wrote split manifest to {MANIFEST}")


if __name__ == "__main__":
    main()
