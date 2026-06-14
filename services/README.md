# services

**Flat** services layer (FastAPI) brought in by the `imp/database` merge. It is
an early variant of the backend and **overlaps with [`../backend/`](../backend/)**
(which is the more complete version organized by packages).

## Contents

| Path | What it is |
|---|---|
| `main.py` | Lifespan: `init_db()` + `chroma.seed()` |
| `routes/session.py` | Session close endpoint (report + email + blob) |
| `ingestion_service.py` | Document ingestion |
| `chroma_service.py`, `blob_service.py`, `email_service.py` | Integrations |
| `agents/cultural.py` | Cultural agent |

## Status

⚠️ Some files are incomplete (e.g. `main.py` assumes undeclared imports).
Before using it seriously, decide whether to **consolidate with `backend/`** or
discard this folder to avoid two sources of truth. See
[`../backend/README.md`](../backend/README.md).
