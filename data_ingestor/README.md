# data_ingestor

Ingestion of **real RAW data** from New York state. Downloads demographics at
the `zip_code` (ZCTA) level from the **US Census ACS5**, maps it to the
`Location` / `LocationStatistics` entities (Marshmallow) and **persists** one per zip.

It is the entry point of the pipeline: it produces the real data on which the
[`data_processor`](../data_processor/) builds the synthetic audience.

## Contents

| Path | What it is |
|---|---|
| `main.py` | Downloads ACS5 (2 requests for all ZCTAs), builds `LocationEntity`, `persist_locations()` per zip and `upload_to_cloud()` to Azure |
| `db.py` | Uploads the Locations to the Azure/Supabase Postgres `locations` table (UPSERT by zip_code) |
| `seed_database.py` | Seeds the generated profiles into the database (used by docker-compose) |
| `dtos/` | Local copy of the entities (self-contained service) |
| `data/nyc_zip_codes.csv` | Input: NY zip codes |
| `components/` | Dapr: `pubsub.yaml` (redis) + `statestore.yaml` (Postgres, persistence in DB) |
| `Dockerfile`, `.dockerignore`, `requirements.txt` | Service packaging |

## How to run

```bash
# Requires CENSUS_DATA_API in .env
python -m data_ingestor.main
# -> writes data_ingestor/data/locations/<zip>.json + _index.json
# -> and uploads each Location to the cloud `locations` table (if a DB URL is set)
```

The persisted output is later consumed by `python -m data_processor`.

## Upload to Azure / Supabase

After saving the JSON copy, `main.py` UPSERTS the Locations into the `locations`
table (schema in [`containers_env/postgresql-db/init.sql`](../containers_env/postgresql-db/init.sql);
apply it once with `apply_schema.py`). Re-running is safe — rows are matched by
`zip_code` and updated, not duplicated.

Environment variables:

| Var | Purpose |
|---|---|
| `DATABASE_POOL_URL` / `DATABASE_URL` | Postgres connection (Azure pooler / Supabase). Read from the repo-root `.env`. If unset, the upload is skipped and only JSON is written. |
| `INGESTOR_UPLOAD` | `auto` (default) uploads when a DB URL exists; set `0` to disable. |
| `DB_SSL` | `require` forces TLS, `disable` turns it off. Auto: TLS for remote hosts, off for localhost. |

A DB failure is logged but does **not** abort ingestion (the JSON copy is kept).

## Notes

- The Dapr state store (`components/statestore.yaml`) is a separate key/value
  cache; the relational upload above writes the queryable `locations` table.
- `data/locations/` is a runtime artifact and is in `.gitignore`.
