from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SOURCE_URL = "https://opendata.arcgis.com/api/v3/datasets/f94e9628f2604e6e9a25fd8c496b4c6c_3/downloads/data?format=geojson&spatialRefId=4326"
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.inventory import (  # noqa: E402
    audit_inventory,
    audit_to_markdown,
    write_audit_json,
)


def main() -> None:
    source = ROOT / "data/raw/ddot_ada_curb_ramps.geojson"
    audit = audit_inventory(source, source_url=SOURCE_URL)
    write_audit_json(audit, ROOT / "data/processed/ddot_inventory_audit.json")
    (ROOT / "data_notes.md").write_text(
        audit_to_markdown(audit),
        encoding="utf-8",
    )
    print(f"Audited {audit.feature_count:,} DDOT curb-ramp records")
    print(f"SHA256 {audit.sha256}")
    print("Wrote data_notes.md and data/processed/ddot_inventory_audit.json")


if __name__ == "__main__":
    main()
