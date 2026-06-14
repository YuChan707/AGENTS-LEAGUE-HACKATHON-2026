"""Upload ingested Locations to the cloud Postgres (Azure / Supabase).

The ingestor builds validated Location entities from the US Census; this module
UPSERTS them into the `locations` table defined in
containers_env/postgresql-db/init.sql. Upsert is keyed on `zip_code`, so the
ingestion can be re-run safely (existing zips are updated, not duplicated).

Connection comes from DATABASE_POOL_URL (preferred, the Azure/Supabase pooler)
or DATABASE_URL. TLS is enabled for remote hosts and skipped for localhost.
Uses SQLAlchemy + asyncpg, the same stack as the backend.
"""

from __future__ import annotations

import json
import os
import ssl
import uuid
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

# Load the repo-root .env (where DATABASE_POOL_URL lives) regardless of cwd.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
# Also load the ingestor's own .env (Census keys, optional DB override).
load_dotenv(Path(__file__).resolve().parent / ".env")


def database_configured() -> bool:
    return bool(os.getenv("DATABASE_POOL_URL") or os.getenv("DATABASE_URL"))


def _db_url() -> str | None:
    url = os.getenv("DATABASE_POOL_URL") or os.getenv("DATABASE_URL")
    if not url or url.startswith("sqlite"):
        return None
    if url.startswith("postgresql+"):
        return url if "+asyncpg" in url else "postgresql+asyncpg://" + url.split("://", 1)[1]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    return url


def _connect_args(url: str) -> dict:
    mode = os.getenv("DB_SSL", "").lower()
    if mode == "disable":
        return {}
    is_local = ("@localhost" in url) or ("@127.0.0.1" in url)
    if mode != "require" and is_local:
        return {}
    ctx = ssl.create_default_context()      # Azure / Supabase require TLS
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return {"ssl": ctx}


# Upsert keyed on zip_code (UNIQUE in the schema). location_id/last_updated are
# passed as native uuid/date objects (see _row); statistics goes as a JSON string
# cast to jsonb.
_UPSERT_SQL = """
INSERT INTO locations (
    location_id, zip_code, country, state, city,
    latitude, longitude, total_population, statistics, last_updated
) VALUES (
    :location_id, :zip_code, :country, :state, :city,
    :latitude, :longitude, :total_population, CAST(:statistics AS jsonb), :last_updated
)
ON CONFLICT (zip_code) DO UPDATE SET
    location_id      = EXCLUDED.location_id,
    country          = EXCLUDED.country,
    state            = EXCLUDED.state,
    city             = EXCLUDED.city,
    latitude         = EXCLUDED.latitude,
    longitude        = EXCLUDED.longitude,
    total_population = EXCLUDED.total_population,
    statistics       = EXCLUDED.statistics,
    last_updated     = EXCLUDED.last_updated
"""


def _as_uuid(value):
    if not value:
        return None
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _as_date(value):
    if not value:
        return None
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _row(record: dict) -> dict:
    coords = record.get("coordinates") or {}
    stats = record.get("statistics")
    return {
        "location_id": _as_uuid(record.get("location_id")),
        "zip_code": record.get("zip_code"),
        "country": record.get("country"),
        "state": record.get("state"),
        "city": record.get("city"),
        "latitude": coords.get("latitude"),
        "longitude": coords.get("longitude"),
        "total_population": record.get("total_population"),
        "statistics": json.dumps(stats) if stats is not None else None,
        "last_updated": _as_date(record.get("last_updated")),
    }


async def upload_locations(records: list[dict]) -> int:
    """UPSERT the dumped Location dicts into the `locations` table. Returns count."""
    url = _db_url()
    if not url:
        raise RuntimeError(
            "No Postgres URL configured. Set DATABASE_POOL_URL or DATABASE_URL "
            "(see containers_env/.env.example)."
        )

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(url, connect_args=_connect_args(url), echo=False)
    stmt = text(_UPSERT_SQL)
    count = 0
    try:
        async with engine.begin() as conn:
            for record in records:
                await conn.execute(stmt, _row(record))
                count += 1
    finally:
        await engine.dispose()
    return count


__all__ = ["upload_locations", "database_configured"]
