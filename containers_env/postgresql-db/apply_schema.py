#!/usr/bin/env python3
"""Apply init.sql (the idempotent OnLooker schema) to Azure / Supabase Postgres.

    python containers_env/postgresql-db/apply_schema.py

Reads DATABASE_POOL_URL (preferred, the Azure/Supabase pooler) or DATABASE_URL
from the environment (.env), and creates every entity table if it does not
exist yet. Safe to run repeatedly (init.sql is all CREATE ... IF NOT EXISTS).

It uses SQLAlchemy + asyncpg — the SAME stack the backend uses to reach the DB —
so the connection string / TLS handling matches the running app exactly.
TLS is enabled for remote hosts (Azure/Supabase) and skipped for sqlite/local.
Override TLS with DB_SSL=require|disable.

Alternative (no Python): paste init.sql into the Supabase SQL editor, or run
    psql "$DATABASE_URL" -f containers_env/postgresql-db/init.sql
"""

from __future__ import annotations

import asyncio
import os
import ssl
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent.parent / ".env")


def _async_url(url: str) -> str:
    """Force the asyncpg driver in the SQLAlchemy URL."""
    if url.startswith("postgresql+asyncpg://") or url.startswith("postgresql+"):
        # already has a driver; only rewrite non-async psycopg drivers
        if "+asyncpg" in url:
            return url
        return "postgresql+asyncpg://" + url.split("://", 1)[1]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    return url


def _resolve_url() -> str:
    url = os.getenv("DATABASE_POOL_URL") or os.getenv("DATABASE_URL")
    if not url:
        sys.exit(
            "Set DATABASE_POOL_URL or DATABASE_URL (the Azure/Supabase Postgres "
            "connection string) in the environment / .env."
        )
    if url.startswith("sqlite"):
        sys.exit(
            "DATABASE_URL points to sqlite. Set the Azure/Supabase Postgres URL "
            "to create the tables there."
        )
    return _async_url(url)


def _connect_args(url: str) -> dict:
    mode = os.getenv("DB_SSL", "").lower()
    if mode == "disable":
        return {}
    is_local = ("@localhost" in url) or ("@127.0.0.1" in url)
    if mode != "require" and is_local:
        return {}  # local Postgres without TLS
    ctx = ssl.create_default_context()      # Azure / Supabase require TLS
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return {"ssl": ctx}


def _split_statements(sql: str) -> list[str]:
    """Split init.sql into individual statements (no PL/pgSQL bodies here)."""
    no_comments = "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )
    return [s.strip() for s in no_comments.split(";") if s.strip()]


async def main() -> None:
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
    except ModuleNotFoundError as exc:
        sys.exit(f"Missing dependency: {exc.name}. Run: pip install sqlalchemy asyncpg")

    url = _resolve_url()
    statements = _split_statements((HERE / "init.sql").read_text(encoding="utf-8"))

    engine = create_async_engine(url, connect_args=_connect_args(url), echo=False)
    try:
        async with engine.begin() as conn:
            for stmt in statements:
                await conn.exec_driver_sql(stmt)
            rows = (
                await conn.execute(
                    text(
                        "SELECT tablename FROM pg_tables "
                        "WHERE schemaname='public' ORDER BY tablename"
                    )
                )
            ).fetchall()
        print(f"Schema applied ({len(statements)} statements). "
              f"{len(rows)} tables in public schema:")
        for (name,) in rows:
            print(f"  - {name}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
