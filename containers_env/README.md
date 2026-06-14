# containers_env

Specs for the **deployment of the external containers** (databases and support
services). These files are not accessed from the app code: they live in the
cloud, deployed with Octopus Deployment.

## Contents

| Path | What it is |
|---|---|
| `docker-compose.yml` | Wires the local stack: `api` + `chromadb` + `data_seeder` |
| `Dockerfile` | Base image of the app |
| `postgresql-db/` | Postgres: `init.sql` (full entity schema), `apply_schema.py` (applies it to Azure/Supabase), `Dockerfile` |
| `embeds-db/` | Config of the embeddings database (ChromaDB) |
| `arm-template.json` | ARM template (Azure) to provision resources |
| `deploy-mcp.ps1` | Deployment script (MCP / Azure) |
| `.env.example` | Safe template of variables (DB, Chroma, LLM, Azure Blob, Data Commons) |

## Usage

```bash
cp containers_env/.env.example containers_env/.env   # fill in real values
docker compose -f containers_env/docker-compose.yml up --build
```

## Database schema (Azure / Supabase Postgres)

`postgresql-db/init.sql` is the idempotent schema: one table per persisted
entity — `locations`, `demographic_groups`, `behavior_formulas`,
`field_behavior_groups`, `group_behavior_profiles`, `audience_specs`,
`audience_segments`, `project_assets`, `reaction_profiles`, plus the backend
operational tables (`audiences`, `sessions`, `analytics`, `ingestion_events`,
`reports`). Rich/nested data is stored as `jsonb`; queryable keys are typed
columns with indexes.

Create/ensure the tables in the cloud DB (reads `DATABASE_POOL_URL` /
`DATABASE_URL`; safe to re-run — `CREATE ... IF NOT EXISTS`):

```bash
python containers_env/postgresql-db/apply_schema.py
# or, with psql / the Supabase SQL editor:
psql "$DATABASE_URL" -f containers_env/postgresql-db/init.sql
```

> The Dapr state stores (`*/components/statestore.yaml`) create their own
> key/value tables separately; the schema above is the queryable relational
> storage per entity.

## Notes

- ~25 GB of space. Use Octopus only for data access/storage.
- **Never** commit the real `.env` (it is in `.gitignore`).
- The Dapr components of each service (`*/components/statestore.yaml`)
  point to this Postgres via `DATABASE_URL`.
