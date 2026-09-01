from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.sampling import sample_one_per_stratum, write_rows  # noqa: E402


def main() -> None:
    source = ROOT / "data/processed/mapillary_coverage_candidates.csv"
    with source.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    sample = sample_one_per_stratum(rows)
    output = ROOT / "data/processed/mapillary_pilot_candidates.csv"
    write_rows(sample, output)
    print(f"Wrote {len(sample)} balanced pilot records to {output}")
    for row in sample:
        print(f"{row['study_area']:35} {row['condition']:15} {row['record_id']}")


if __name__ == "__main__":
    main()
