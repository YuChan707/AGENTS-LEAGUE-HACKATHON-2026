# backend

OnLooker **FastAPI** API: orchestrates the AI agents, exposes the routes
consumed by the front-end ([`../ui-onlooker/`](../ui-onlooker/)) and persists
sessions/reports. It serves the analysis of a digital product against the
synthetic audience.

## Structure

| Path | What it is |
|---|---|
| `main.py` | FastAPI app: lifespan (DB/Chroma), CORS, routers. Runs with `uvicorn backend.main:app` |
| `agents/` | Agents: `audience`, `coaching`, `cultural`, `document_analyst`, `feedback`, `vision`, `speech`, `orchestrator` |
| `routes/` | Endpoints: `session`, `stream`, `analyze`, `document`, `feedback`, `health` |
| `services/` | Integrations: `chroma_service`, `blob_service`, `email_service`, `ingestion_service`, `document_service`, `pptx_generator`, `llm_factory` |
| `models/database.py`, `database.py` | Models and SQLAlchemy engine (async) |
| `components/statestore.yaml` | Dapr state store -> Postgres |
| `Dockerfile`, `.dockerignore`, `requirements.txt` | Service packaging |

## How to run

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000

# Docker (build from the ROOT of the repo, needs dtos/):
docker build -f backend/Dockerfile -t onlooker-backend .
```

## Notes

- It imports the shared package [`../dtos/`](../dtos/); that is why the Docker build
  uses the repo root as context.
- Per-environment config (DB, Chroma, Azure Blob, LLM): see
  [`../containers_env/.env.example`](../containers_env/.env.example).
- There is a parallel layer in [`../services/`](../services/) that overlaps with this one;
  see its README.
