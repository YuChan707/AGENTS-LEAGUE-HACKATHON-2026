import httpx
import asyncio

GEO_ID = "geoId/3651000"
VARIABLES = {
    "Count_Person_25To34Years": "marketing_young_professional",
    "Count_Person_EducationalAttainment_BachelorOrHigher": "marketing_educated",
    "Median_Income_Person": "finance_income_median",
    "Count_Person_Employed": "finance_employed",
    "Count_Person_SelfEmployed": "business_self_employed",
}

async def fetch_place_statistics(geo_id: str = GEO_ID) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://api.datacommons.org/v2/observation/point/bulk",
            params={"entities": geo_id, "variables": list(VARIABLES.keys()), "date": "latest"}
        )
        response.raise_for_status()
        raw = response.json()
    results = {}
    for variable, friendly in VARIABLES.items():
        try:
            obs = raw["observationsByVariable"][variable]["byEntity"][geo_id]
            results[friendly] = obs["orderedFacets"][0]["observations"][0]["value"]
        except (KeyError, IndexError):
            results[friendly] = None
    return results

if __name__ == "__main__":
    stats = asyncio.run(fetch_place_statistics())
    print(stats)
