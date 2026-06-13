import os
import json
import uuid

import pandas as pd
from datacommons_client.client import DataCommonsClient
from dapr.clients import DaprClient
from datetime import datetime
import asyncio
from tqdm.asyncio import tqdm_asyncio
from asyncio import create_task
from dtos.data_ingestors import Location, GeoPoint
from datetime import datetime
from zoneinfo import ZoneInfo

sitemap_zip_codes= pd.read_csv("data/nyc_zip_codes.csv")
DATA_COMMONS_API = os.getenv("DATA_COMMONS_API")

# Nombre del componente de estado que definas en tu archivo state.yaml de Dapr
DAPR_STORE_NAME = "statestore" 

def data_extractor_client():
    return DataCommonsClient(api_key=DATA_COMMONS_API)

def dapr_client():
    # Inicializa el cliente Dapr. Por defecto, busca el sidecar en localhost:50001 (gRPC)
    return DaprClient()

async def process_sitemaps():
    for i in tqdm_asyncio.range(len(sitemap_zip_codes),desc="Procesando Sitemaps"):
        row = sitemap_zip_codes[i]

        cord = GeoPoint()
        cord.latitude = row["lat"]
        cord.longitude = row["lng"]

        location = Location()
        location.location_name = row["city"]
        location.coordinates = cord

        location.zip_code = row["zip"]
        location.country = "US"
        location.state = row["state_name"]
        location.city = row["city"]

        location.last_updated = datetime.now(
            ZoneInfo("America/New_York")
        )
        location.location_id = str(uuid.uuid1(location.zip_code, ))

        await asyncio.sleep(0.5)


def main() -> None:
    # 1. Inicializar clientes
    dc_client = data_extractor_client()
    
    # 2. Definir entidad geográfica (New York City)
    nyc_dcid = ["geoId/3651000"]
    
    # 3. Definir variables estadísticas
    features = [
        "Count_Person",                        # Total Population
        "Median_Income_Household",             # Median Household Income
        "Median_Age_Person"                    # Median Age
    ]
    
    print("Fetching demographic time series for New York City...")
    
    # 4. Extracción de datos
    df = dc_client.observations_dataframe(
        entity_dcids=nyc_dcid,
        variable_dcids=features,
        date="all"
    )
    
    # 5. Limpieza y procesamiento de datos
    if not df.empty:
        print("\nData successfully retrieved! Processing...")
        
        processed_df = df.pivot(index="date", columns="variable", values="value")
        processed_df = processed_df.rename(columns={
            "Count_Person": "Total Population",
            "Median_Income_Household": "Median Income ($)",
            "Median_Age_Person": "Median Age"
        })
        processed_df = processed_df.sort_index()
        
        print("\n--- New York City Demographic Timeline ---")
        print(processed_df.tail(10))
        
        # --- NUEVA LÓGICA DE DAPR: Guardar en el State Store ---
        print("\nSaving demographic data to Dapr State Store...")
        
        # Convertimos el índice de fechas en una columna para iterar fácilmente
        processed_df = processed_df.reset_index()
        
        with dapr_client() as d_client:
            for _, row in processed_df.iterrows():
                ano = str(row['date'])
                
                # Creamos el payload con los datos de ese año en específico
                payload = {
                    "total_population": float(row['Total Population']) if pd.notna(row['Total Population']) else None,
                    "median_income": float(row['Median Income ($)']) if pd.notna(row['Median Income ($)']) else None,
                    "median_age": float(row['Median Age']) if pd.notna(row['Median Age']) else None
                }
                
                # Generamos una clave única en el formato: "nyc_demographics_2020"
                state_key = f"nyc_demographics_{ano}"
                
                # Guardamos el estado usando el cliente de Dapr
                d_client.save_state(
                    store_name=DAPR_STORE_NAME,
                    key=state_key,
                    value=json.dumps(payload)
                )
                
            print(f"Successfully saved {len(processed_df)} years of data to Dapr!")
            
    else:
        print("No data returned. Please verify your API key or DCIDs.")

if __name__ == "__main__":
    main()