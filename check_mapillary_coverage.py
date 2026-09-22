import argparse
from pathlib import Path
import collections
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.mapillary import run_coverage_check  # noqa: E402
from curb_ramp_eval.local_config import load_local_env  # noqa: E402


def main() -> None:
    load_local_env(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Check Mapillary coverage around sampled DDOT curb ramps")
    parser.add_argument("--max-points", type=int, default=None)
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Discard an existing partial output and query every candidate again",
    )
    parser.add_argument(
        "--candidate-file",
        type=Path,
        default=ROOT / "data/processed/mapillary_coverage_candidates.csv",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=ROOT / "data/processed/mapillary_coverage_results.csv",
    )
    args = parser.parse_args()

    results = run_coverage_check(
        args.candidate_file,
        args.output_file,
        max_points=args.max_points,
        resume=not args.no_resume,
    )
    totals = collections.defaultdict(lambda: {"points": 0, "covered": 0, "images": 0})
    for row in results:
        values = totals[row["study_area"]]
        values["points"] += 1
        values["covered"] += int(row["coverage_available"])
        values["images"] += int(row["image_count"])

    print("\nCoverage summary")
    for area, values in sorted(totals.items()):
        rate = values["covered"] / values["points"] if values["points"] else 0
        print(f"{area}: {values['covered']}/{values['points']} covered ({rate:.1%}), {values['images']} images")


if __name__ == "__main__":
    main()
