from pathlib import Path
import collections
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.sampling import (  # noqa: E402
    inventory_rows,
    load_study_areas,
    sample_coverage_candidates,
    write_rows,
)


def main() -> None:
    rows = inventory_rows(ROOT / "data/raw/ddot_ada_curb_ramps.geojson")
    areas = load_study_areas(ROOT / "config/study_areas.json")
    sample = sample_coverage_candidates(rows, areas)
    output = ROOT / "data/processed/mapillary_coverage_candidates.csv"
    write_rows(sample, output)

    counts = collections.Counter((row["study_area"], row["condition"]) for row in sample)
    print(f"Wrote {len(sample)} seeded coverage candidates to {output}")
    for key, value in sorted(counts.items()):
        print(f"{key[0]:35} {key[1]:15} {value:3}")


if __name__ == "__main__":
    main()

