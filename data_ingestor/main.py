import asyncio
import os
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
from census import Census
from tqdm import tqdm
from dotenv import load_dotenv

# Adjust these imports to the real ones of your DTOs and Schemas
from marshmallow import ValidationError

# Loads the .env variables (CENSUS_DATA_API, etc.) into the environment.
load_dotenv()

from dtos.data_ingestors import Location, LocationEntity

# Marshmallow schemas are reusable: they are instantiated once.
_location_schema = Location()


# Safe conversion functions to avoid crashes due to empty strings from the API
def safe_float(val, default=0.0):
    if val is None or str(val).strip() in ["", "-", "None"]: return default
    try:
        return float(val)
    except ValueError:
        return default


def safe_int(val, default=0):
    if val is None or str(val).strip() in ["", "-", "None"]: return default
    try:
        return int(val)
    except ValueError:
        return default


def data_extractor_client():
    # The real name of the variable in the .env is CENSUS_DATA_API.
    api_key = os.getenv("CENSUS_DATA_API") or os.getenv("CENSUS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing Census API key. Define CENSUS_DATA_API in the .env "
            "(the Census API requires a key since May 2026)."
        )
    return Census(key=api_key)


# Variables we request from each dataset (module-level constants).
VARS_BASICS = (
    'B01001_001E', 'B01001_002E', 'B01001_026E', 'B19013_001E',
    'B25010_001E', 'B25077_001E', 'B03002_003E', 'B03002_004E',
    'B03002_006E', 'B03002_012E', 'B01001_003E', 'B01001_004E',
    'B01001_005E', 'B01001_006E', 'B01001_027E', 'B01001_028E',
    'B01001_029E', 'B01001_030E',
)
VARS_SUBJECT = ('S2301_C04_001E', 'S1701_C03_001E', 'S1501_C02_015E')

# Name of the geographic column that the Census returns for ZCTA queries.
ZCTA_KEY = "zip code tabulation area"


async def fetch_census_tables(client, vars_basics=VARS_BASICS, vars_subject=VARS_SUBJECT):
    """Downloads ALL ZCTA at once (2 requests in total, not 2 per ZIP).

    Returns two dicts indexed by ZIP code to cross-reference later in memory.
    """
    loop = asyncio.get_running_loop()
    # The wildcard '*' brings all ZCTA in a single request per dataset.
    geo_config = {'for': f'{ZCTA_KEY}:*'}

    def call_basics():
        return client.acs5.get(tuple(vars_basics), geo_config)

    def call_subject():
        # The "subject" tables (S2301..., S1701..., S1501...) live in the
        # acs5st client (dataset acs5/subject), NOT in client.acs5.subject.
        return client.acs5st.get(tuple(vars_subject), geo_config)

    res_basico, res_subject = await asyncio.gather(
        loop.run_in_executor(None, call_basics),
        loop.run_in_executor(None, call_subject),
    )

    basics_by_zip = {rec.get(ZCTA_KEY): rec for rec in (res_basico or [])}
    subject_by_zip = {rec.get(ZCTA_KEY): rec for rec in (res_subject or [])}
    return basics_by_zip, subject_by_zip


def build_location_metadata(data_b: dict, data_s: dict) -> dict:
    """Parses the already-downloaded records of a ZIP. Makes no request."""
    if not data_b or not data_s:
        return {}

    try:
        # --- Demographic Processing ---
        total_pop = safe_float(data_b.get('B01001_001E'), default=1.0)
        if total_pop == 0: total_pop = 1.0  # Avoid division by zero

        pct_male = (safe_float(data_b.get('B01001_002E')) / total_pop) * 100
        pct_female = (safe_float(data_b.get('B01001_026E')) / total_pop) * 100

        valor_vivienda_local = safe_float(data_b.get('B25077_001E'), default=280000.0)
        calculated_cost_of_living = (valor_vivienda_local / 280000.0) * 100
        calculated_cost_of_living = max(60.0, min(250.0, calculated_cost_of_living))

        ethnicity = {
            "white": (safe_float(data_b.get('B03002_003E')) / total_pop) * 100,
            "black": (safe_float(data_b.get('B03002_004E')) / total_pop) * 100,
            "asian": (safe_float(data_b.get('B03002_006E')) / total_pop) * 100,
            "hispanic": (safe_float(data_b.get('B03002_012E')) / total_pop) * 100,
            "other": 0.0
        }
        sum_known = ethnicity["white"] + ethnicity["black"] + ethnicity["asian"] + ethnicity["hispanic"]
        ethnicity["other"] = max(0.0, 100.0 - sum_known)

        hombres_menores = sum(safe_float(data_b.get(f'B01001_00{i}E')) for i in range(3, 7))
        mujeres_menores = sum(safe_float(data_b.get(f'B01001_02{i}E')) for i in range(7, 10)) + safe_float(
            data_b.get('B01001_030E'))
        total_under_18 = hombres_menores + mujeres_menores

        age_ranges_mapped = {
            "under_18": (total_under_18 / total_pop) * 100,
            "over_18": (100.0 - ((total_under_18 / total_pop) * 100))
        }

        entity_data = {
            "unemployment_rate": safe_float(data_s.get('S2301_C04_001E')),
            "poverty_rate": safe_float(data_s.get('S1701_C03_001E')),
            "cost_of_living_index": round(calculated_cost_of_living, 2),
            "median_income": safe_int(data_b.get('B19013_001E')),
            "avg_household_size": safe_float(data_b.get('B25010_001E')),
            "safety_index": 75.0,
            "avg_education": safe_float(data_s.get('S1501_C02_015E')),
            "avg_female_population": round(pct_female, 2),
            "avg_male_population": round(pct_male, 2),
            "age_ranges": age_ranges_mapped,
            "ethnicity_distribution": ethnicity
        }

        return entity_data

    except Exception as e:
        # We include the type so we don't hide errors like AttributeError again.
        print(f"Error parsing metadata: {type(e).__name__}: {e}")
        return {}


def create_location(_logger, row, basics_by_zip: dict, subject_by_zip: dict) -> LocationEntity | None:
    zip_code = str(row.zip)
    # In-memory cross-reference: zero requests here, the data was already downloaded in bulk.
    metadata = build_location_metadata(
        basics_by_zip.get(zip_code, {}),
        subject_by_zip.get(zip_code, {}),
    )

    # We build the payload as a dict and let Marshmallow validate and
    # produce the LocationEntity via @post_load (load(), not assigning attributes).
    payload = {
        "location_id": str(uuid.uuid4()),
        "coordinates": {
            "latitude": float(row.lat),
            "longitude": float(row.lng),
        },
        "zip_code": zip_code,
        "country": "US",
        "state": row.state_name,
        "city": row.city,
        "total_population": int(row.population),
        "last_updated": datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
    }
    if metadata:
        payload["statistics"] = metadata

    try:
        location = _location_schema.load(payload)
    except ValidationError as err:
        _logger.warning(f"Zip {row.zip} discarded due to validation: {err.messages}")
        return None

    _logger.info(f"New Location Created for Zip {row.zip}")
    return location


async def process_sitemaps(_logger, dc_client, sitemap_zip_codes):
    # 2 requests in total: we download all ZCTA only once.
    _logger.info("Downloading Census tables (2 requests for all ZCTA)...")
    basics_by_zip, subject_by_zip = await fetch_census_tables(dc_client)
    _logger.info(
        f"Tables downloaded: {len(basics_by_zip)} ZCTA basics, "
        f"{len(subject_by_zip)} ZCTA subject."
    )

    # The rest is CPU/memory: we build and validate each Location without further requests.
    locations = []
    for row in tqdm(sitemap_zip_codes.itertuples(index=True), desc="SitemapProcessing"):
        loc = create_location(_logger, row, basics_by_zip, subject_by_zip)
        if loc is not None:
            locations.append(loc)
    return locations


# Persistence folder: data_ingestor/data/locations/ (one JSON per zip_code).
LOCATIONS_DIR = Path(__file__).resolve().parent / "data" / "locations"


def persist_locations(_logger, locations) -> list[dict]:
    """Persists each LocationEntity as JSON per zip_code + an index.

    Runs when it finishes processing ALL groups by zip_code. Dumps the
    Marshmallow-validated entity (.dump) to preserve the contract. Returns the
    dumped records so they can also be uploaded to the cloud DB.
    """
    LOCATIONS_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    index = []
    for loc in locations:
        record = _location_schema.dump(loc)
        zip_code = record.get("zip_code") or "unknown"
        path = LOCATIONS_DIR / f"{zip_code}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        records.append(record)
        index.append(
            {
                "zip_code": zip_code,
                "location_id": record.get("location_id"),
                "city": record.get("city"),
                "state": record.get("state"),
                "has_statistics": bool(record.get("statistics")),
            }
        )
    index_path = LOCATIONS_DIR / "_index.json"
    index_path.write_text(
        json.dumps({"count": len(index), "locations": index}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _logger.info(f"Persisted {len(index)} locations in {LOCATIONS_DIR}")
    return records


async def upload_to_cloud(_logger, records: list[dict]) -> None:
    """Uploads the locations to the Azure/Supabase Postgres `locations` table.

    Controlled by INGESTOR_UPLOAD (default "auto"): uploads when a DB URL is
    configured, skips with a warning otherwise. Set INGESTOR_UPLOAD=0 to disable.
    A DB failure is logged but does NOT abort the ingestion (JSON is already saved).
    """
    try:
        from db import database_configured, upload_locations
    except ImportError:  # when run as `python -m data_ingestor.main` from repo root
        from data_ingestor.db import database_configured, upload_locations

    flag = os.getenv("INGESTOR_UPLOAD", "auto").lower()
    if flag in ("0", "false", "no", "off"):
        _logger.info("DB upload disabled (INGESTOR_UPLOAD=%s).", flag)
        return
    if not database_configured():
        _logger.warning(
            "No DATABASE_URL/DATABASE_POOL_URL set -> skipping Azure upload "
            "(locations are saved as JSON). See containers_env/.env.example."
        )
        return
    try:
        n = await upload_locations(records)
        _logger.info("Uploaded %d locations to the cloud Postgres (locations table).", n)
    except Exception as exc:  # noqa: BLE001 - do not lose the run over a DB hiccup
        _logger.error("Azure upload failed (%s: %s). JSON copy is intact.", type(exc).__name__, exc)


async def main(_logger) -> None:
    _logger.info("Initializing Census Bureau Client")
    dc_client = data_extractor_client()

    # Load your local data CSV
    sitemap_zip_codes = pd.read_csv("data/nyc_zip_codes.csv")

    resultant = await process_sitemaps(_logger, dc_client, sitemap_zip_codes)
    _logger.info(f"Process finished. {len(resultant)} Marshmallow entities ready.")

    # Finished processing all groups by zip_code -> persist locally + upload to Azure.
    records = persist_locations(_logger, resultant)
    await upload_to_cloud(_logger, records)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("DemographicsApp")
    logger.info("INIT DEMOGRAPHICS DATA EXTRACTION")
    asyncio.run(main(_logger=logger))