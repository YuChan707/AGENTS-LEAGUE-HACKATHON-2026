import asyncio
import os
import uuid
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from census import Census
from tqdm import tqdm
from dotenv import load_dotenv

# Ajusta estas importaciones a las reales de tus DTOs y Schemas
from marshmallow import ValidationError

# Carga las variables del .env (CENSUS_DATA_API, etc.) al entorno.
load_dotenv()

from dtos.data_ingestors import Location, LocationEntity

# Los esquemas Marshmallow son reutilizables: se instancian una vez.
_location_schema = Location()


# Funciones seguras de conversión para evitar caídas por strings vacíos de la API
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
    # El nombre real de la variable en el .env es CENSUS_DATA_API.
    api_key = os.getenv("CENSUS_DATA_API") or os.getenv("CENSUS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta la API key del Census. Define CENSUS_DATA_API en el .env "
            "(la API del Census exige key desde mayo 2026)."
        )
    return Census(key=api_key)


# Variables que pedimos a cada dataset (constantes a nivel de módulo).
VARS_BASICS = (
    'B01001_001E', 'B01001_002E', 'B01001_026E', 'B19013_001E',
    'B25010_001E', 'B25077_001E', 'B03002_003E', 'B03002_004E',
    'B03002_006E', 'B03002_012E', 'B01001_003E', 'B01001_004E',
    'B01001_005E', 'B01001_006E', 'B01001_027E', 'B01001_028E',
    'B01001_029E', 'B01001_030E',
)
VARS_SUBJECT = ('S2301_C04_001E', 'S1701_C03_001E', 'S1501_C02_015E')

# Nombre de la columna geográfica que devuelve el Census para consultas ZCTA.
ZCTA_KEY = "zip code tabulation area"


async def fetch_census_tables(client, vars_basics=VARS_BASICS, vars_subject=VARS_SUBJECT):
    """Descarga TODOS los ZCTA de una sola vez (2 requests en total, no 2 por ZIP).

    Devuelve dos dicts indexados por código ZIP para cruzar luego en memoria.
    """
    loop = asyncio.get_running_loop()
    # El comodín '*' trae todos los ZCTA en una sola petición por dataset.
    geo_config = {'for': f'{ZCTA_KEY}:*'}

    def call_basics():
        return client.acs5.get(tuple(vars_basics), geo_config)

    def call_subject():
        # Las tablas "subject" (S2301..., S1701..., S1501...) viven en el
        # cliente acs5st (dataset acs5/subject), NO en client.acs5.subject.
        return client.acs5st.get(tuple(vars_subject), geo_config)

    res_basico, res_subject = await asyncio.gather(
        loop.run_in_executor(None, call_basics),
        loop.run_in_executor(None, call_subject),
    )

    basics_by_zip = {rec.get(ZCTA_KEY): rec for rec in (res_basico or [])}
    subject_by_zip = {rec.get(ZCTA_KEY): rec for rec in (res_subject or [])}
    return basics_by_zip, subject_by_zip


def build_location_metadata(data_b: dict, data_s: dict) -> dict:
    """Parsea los registros ya descargados de un ZIP. No hace ninguna request."""
    if not data_b or not data_s:
        return {}

    try:
        # --- Procesamiento Demográfico ---
        total_pop = safe_float(data_b.get('B01001_001E'), default=1.0)
        if total_pop == 0: total_pop = 1.0  # Evitar división por cero

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
        # Incluimos el tipo para no volver a ocultar errores como AttributeError.
        print(f"Error parseando metadatos: {type(e).__name__}: {e}")
        return {}


def create_location(_logger, row, basics_by_zip: dict, subject_by_zip: dict) -> LocationEntity | None:
    zip_code = str(row.zip)
    # Cruce en memoria: cero requests aquí, los datos ya se descargaron en bloque.
    metadata = build_location_metadata(
        basics_by_zip.get(zip_code, {}),
        subject_by_zip.get(zip_code, {}),
    )

    # Construimos el payload como dict y dejamos que Marshmallow valide y
    # produzca el LocationEntity vía @post_load (load(), no asignar atributos).
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
        _logger.warning(f"Zip {row.zip} descartado por validación: {err.messages}")
        return None

    _logger.info(f"Nueva Ubicación Creada para Zip {row.zip}")
    return location


async def process_sitemaps(_logger, dc_client, sitemap_zip_codes):
    # 2 requests en total: descargamos todos los ZCTA una sola vez.
    _logger.info("Descargando tablas del Census (2 requests para todos los ZCTA)...")
    basics_by_zip, subject_by_zip = await fetch_census_tables(dc_client)
    _logger.info(
        f"Tablas descargadas: {len(basics_by_zip)} ZCTA basics, "
        f"{len(subject_by_zip)} ZCTA subject."
    )

    # El resto es CPU/memoria: construimos y validamos cada Location sin más requests.
    locations = []
    for row in tqdm(sitemap_zip_codes.itertuples(index=True), desc="SitemapProcessing"):
        loc = create_location(_logger, row, basics_by_zip, subject_by_zip)
        if loc is not None:
            locations.append(loc)
    return locations


async def main(_logger) -> None:
    _logger.info("Inicializando Census Bureau Client")
    dc_client = data_extractor_client()

    # Carga tu CSV de datos locales
    sitemap_zip_codes = pd.read_csv("data/nyc_zip_codes.csv")

    resultant = await process_sitemaps(_logger, dc_client, sitemap_zip_codes)
    _logger.info(f"Proceso finalizado. {len(resultant)} entidades Marshmallow listas.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("DemographicsApp")
    logger.info("INIT DEMOGRAPHICS DATA EXTRACTION")
    asyncio.run(main(_logger=logger))