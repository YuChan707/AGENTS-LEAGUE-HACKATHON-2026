"""JSON file persistence for the audience pipeline.

A deliberate choice for the hackathon: JSON files, zero infrastructure, runs on
any machine and is easy to inspect/demo. The save points are isolated here so we
can switch to Postgres / ChromaDB / Dapr state store without touching the
pipeline logic.

Layout (repo root, override with ONLOOKER_DATA_DIR):

    data_ingestor/data/locations/<zip>.json      <- LocationEntity by zip_code
    data_ingestor/data/locations/_index.json     <- index {zip, location_id, city}
    data_processor/output/behavior_model/<zip>.json
    data_processor/output/field_groups/<zip>.json
    data_processor/output/group_profiles/<zip>.json
    data_processor/output/audience_specs/<zip>.json   <- consolidated general spec
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_ROOT = Path(os.getenv("ONLOOKER_DATA_DIR", str(Path(__file__).resolve().parent.parent)))

LOCATIONS_DIR = _ROOT / "data_ingestor" / "data" / "locations"
PROCESSOR_OUT_DIR = _ROOT / "data_processor" / "output"


def _dump(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # default=str serializes UUID and date (marshmallow deserializes them to objects).
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Locations (data_ingestor)
# ---------------------------------------------------------------------------
def save_locations(locations: list[dict]) -> Path:
    """Persist a list of Locations (dicts) by zip_code + an index."""
    index = []
    for loc in locations:
        zip_code = loc.get("zip_code") or "unknown"
        _dump(LOCATIONS_DIR / f"{zip_code}.json", loc)
        index.append(
            {
                "zip_code": zip_code,
                "location_id": loc.get("location_id"),
                "city": loc.get("city"),
                "state": loc.get("state"),
                "has_statistics": bool(loc.get("statistics")),
            }
        )
    _dump(LOCATIONS_DIR / "_index.json", {"count": len(index), "locations": index})
    return LOCATIONS_DIR


def load_locations() -> list[dict]:
    """Load all persisted Locations (ignores the index)."""
    if not LOCATIONS_DIR.exists():
        return []
    out = []
    for p in sorted(LOCATIONS_DIR.glob("*.json")):
        if p.name == "_index.json":
            continue
        out.append(_load(p))
    return out


def load_location(zip_code: str) -> dict | None:
    p = LOCATIONS_DIR / f"{zip_code}.json"
    return _load(p) if p.exists() else None


# ---------------------------------------------------------------------------
# data_processor outputs
# ---------------------------------------------------------------------------
def save_processor_output(subdir: str, key: str, obj) -> Path:
    return _dump(PROCESSOR_OUT_DIR / subdir / f"{key}.json", obj)


def save_audience_specs(zip_code: str, spec: dict) -> Path:
    """Consolidated general spec of a location's audience groups."""
    return save_processor_output("audience_specs", zip_code, spec)


__all__ = [
    "LOCATIONS_DIR",
    "PROCESSOR_OUT_DIR",
    "save_locations",
    "load_locations",
    "load_location",
    "save_processor_output",
    "save_audience_specs",
]
