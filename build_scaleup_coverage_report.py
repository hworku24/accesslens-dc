from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEVELOPMENT = ROOT / "data/processed/mapillary_scaleup_development_coverage.csv"
HELD_OUT = ROOT / "data/processed/mapillary_scaleup_heldout_coverage.csv"
OUTPUT = ROOT / "outputs/sprint5_coverage_report.md"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def coverage_counts(rows: list[dict], field: str) -> list[tuple[str, int, int]]:
    totals = Counter(row[field] for row in rows)
    covered = Counter(row[field] for row in rows if row["coverage_available"] == "1")
    return [(name, covered[name], totals[name]) for name in sorted(totals)]


def date_range(rows: list[dict]) -> tuple[str, str]:
    values = []
    for row in rows:
        for field in ("oldest_captured_at", "newest_captured_at"):
            if row.get(field):
                values.append(int(row[field]))
    if not values:
        return "n/a", "n/a"
    render = lambda value: datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()
    return render(min(values)), render(max(values))


def render_section(name: str, rows: list[dict]) -> list[str]:
    covered = sum(row["coverage_available"] == "1" for row in rows)
    oldest, newest = date_range(rows)
    lines = [
        f"## {name}",
        "",
        f"- Covered locations: {covered}/{len(rows)} ({covered / len(rows):.1%})",
        f"- API candidate images: {sum(int(row['image_count']) for row in rows):,}",
        f"- Capture-date range: {oldest} to {newest}",
        "",
        "### By study area",
        "",
        "| Study area | Covered | Rate |",
        "|---|---:|---:|",
    ]
    for label, count, total in coverage_counts(rows, "study_area"):
        lines.append(f"| {label.replace('_', ' ')} | {count}/{total} | {count / total:.1%} |")
    lines.extend(
        [
            "",
            "### By inventory condition",
            "",
            "| Condition | Covered | Rate |",
            "|---|---:|---:|",
        ]
    )
    for label, count, total in coverage_counts(rows, "condition"):
        lines.append(f"| {label} | {count}/{total} | {count / total:.1%} |")
    lines.append("")
    return lines


def main() -> None:
    development = read_csv(DEVELOPMENT)
    held_out = read_csv(HELD_OUT)
    lines = [
        "# Sprint 5: scale-up coverage",
        "",
        "",
        "The held-out check records metadata only. Held-out imagery remains unopened during",
        "development labeling and threshold work.",
        "",
    ]
    lines.extend(render_section("Development split", development))
    lines.extend(render_section("Held-out split", held_out))
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
