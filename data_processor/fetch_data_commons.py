"""Fetch raw statistics from the Data Commons API (v2 REST).

Goal of this module: pull location-level demographics for every ZIP code
(ZCTA) in New York state (geoId/36) and map them onto the `Location` /
`LocationStatistics` entities defined in dtos/data_ingestors.py.

Run as a script it acts as an AVAILABILITY PROBE: for a sample NY ZIP it asks
Data Commons which of the statistical variables we need actually exist, and
prints a coverage report. This is the "prueba" step before the full extraction.

    export DATACOMMONS_API_KEY=...   # free key from https://apikeys.datacommons.org
    python -m data_processor.fetch_data_commons            # probe sample ZIP 10001
    python -m data_processor.fetch_data_commons zip/11201  # probe another ZIP

Stdlib only (urllib + json) so it runs without installing anything.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = "https://api.datacommons.org/v2"
NY_STATE_DCID = "geoId/36"          # New York state
SAMPLE_ZIP = "zip/10001"           # Manhattan (Chelsea) — sample for the probe

# ---------------------------------------------------------------------------
# Candidate statistical variables for each LocationStatistics field.
# We list MULTIPLE candidates per field on purpose: the probe tells us which
# ones Data Commons actually serves at ZCTA level so we can lock the mapping.
# Fields with no expected direct StatVar (cost_of_living_index, safety_index)
# are listed so the report flags them explicitly as "needs another source".
# ---------------------------------------------------------------------------
STATVAR_CANDIDATES: dict[str, list[str]] = {
    "total_population": ["Count_Person"],
    "median_income": [
        "Median_Income_Household",
        "Median_Income_Person",
    ],
    "unemployment_rate": [
        "UnemploymentRate_Person",                 # direct rate (may be county+ only)
        "Count_Person_Unemployed",                 # fallback: derive from components
        "Count_Person_InLaborForce",
    ],
    "poverty_rate": [
        "Count_Person_BelowPovertyLevelInThePast12Months",   # count -> derive % vs total
        "Percent_Person_BelowPovertyLevelInThePast12Months",
    ],
    "avg_household_size": [
        "Mean_HouseholdSize",                      # direct (may not exist at ZCTA)
        "Count_Household",                         # fallback: Count_Person / Count_Household
        "Count_Person_InHouseholds",
    ],
    "sex_distribution": [
        "Count_Person_Male",
        "Count_Person_Female",
    ],
    "avg_education": [
        "Count_Person_EducationalAttainmentRegularHighSchoolDiploma",
        "Count_Person_EducationalAttainmentBachelorsDegree",
        "Count_Person_EducationalAttainmentMastersDegree",
        "Count_Person_EducationalAttainmentDoctorateDegree",
        "Count_Person_25OrMoreYears",              # denominator for attainment shares
    ],
    "age_ranges": [
        "Count_Person_Upto5Years",
        "Count_Person_5To17Years",
        "Count_Person_18To24Years",
        "Count_Person_25To34Years",
        "Count_Person_35To44Years",
        "Count_Person_45To54Years",
        "Count_Person_55To64Years",
        "Count_Person_65To74Years",
        "Count_Person_75OrMoreYears",
    ],
    "ethnicity_distribution": [
        "Count_Person_WhiteAlone",
        "Count_Person_BlackOrAfricanAmericanAlone",
        "Count_Person_AsianAlone",
        "Count_Person_AmericanIndianAndAlaskaNativeAlone",
        "Count_Person_NativeHawaiianAndOtherPacificIslanderAlone",
        "Count_Person_SomeOtherRaceAlone",
        "Count_Person_TwoOrMoreRaces",
        "Count_Person_HispanicOrLatino",
    ],
    # No expected direct StatVar in Data Commons — flagged by the probe:
    "cost_of_living_index": [],
    "safety_index": [],
}

# Node properties needed for the Location identity / GeoPoint.
NODE_PROPERTIES = ["name", "latitude", "longitude", "containedInPlace"]


class DataCommonsError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("DATACOMMONS_API_KEY", "").strip()
    if not key:
        raise DataCommonsError(
            "DATACOMMONS_API_KEY is not set. Get a free key at "
            "https://apikeys.datacommons.org and `export DATACOMMONS_API_KEY=...`"
        )
    return key


def _post(path: str, body: dict) -> dict:
    """POST a JSON body to the v2 API and return the parsed JSON response."""
    url = f"{API_BASE}/{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": _api_key(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise DataCommonsError(f"HTTP {e.code} from {path}: {detail}") from e
    except urllib.error.URLError as e:
        raise DataCommonsError(f"Network error calling {path}: {e.reason}") from e


# ---------------------------------------------------------------------------
# Observation (statistical variable) queries
# ---------------------------------------------------------------------------
def fetch_observations(entity: str, variables: list[str]) -> dict[str, dict]:
    """Return {statvar: {value, date}} for the variables that have a LATEST
    observation for `entity`. Missing/unavailable variables are omitted."""
    if not variables:
        return {}
    resp = _post(
        "observation",
        {
            "select": ["date", "variable", "entity", "value"],
            "entity": {"dcids": [entity]},
            "variable": {"dcids": variables},
            "date": "LATEST",
        },
    )
    out: dict[str, dict] = {}
    by_variable = resp.get("byVariable", {})
    for sv, vblock in by_variable.items():
        ent = vblock.get("byEntity", {}).get(entity, {})
        series = ent.get("orderedFacets") or []
        for facet in series:
            obs = facet.get("observations") or []
            if obs:
                out[sv] = {"value": obs[-1].get("value"), "date": obs[-1].get("date")}
                break
    return out


def fetch_node_props(entity: str, props: list[str]) -> dict[str, object]:
    """Return {property: value(s)} for the requested node properties."""
    expr = "->[" + ", ".join(props) + "]"
    resp = _post("node", {"nodes": [entity], "property": expr})
    arcs = resp.get("data", {}).get(entity, {}).get("arcs", {})
    out: dict[str, object] = {}
    for prop, block in arcs.items():
        nodes = block.get("nodes", [])
        vals = [n.get("value") or n.get("name") or n.get("dcid") for n in nodes]
        out[prop] = vals if len(vals) != 1 else vals[0]
    return out


def list_ny_zctas() -> list[str]:
    """List the ZCTA (ZIP) DCIDs contained in New York state."""
    resp = _post(
        "node",
        {
            "nodes": [NY_STATE_DCID],
            "property": "<-containedInPlace+{typeOf:CensusZipCodeTabulationArea}",
        },
    )
    arcs = resp.get("data", {}).get(NY_STATE_DCID, {}).get("arcs", {})
    zctas: list[str] = []
    for block in arcs.values():
        for n in block.get("nodes", []):
            dcid = n.get("dcid")
            if dcid:
                zctas.append(dcid)
    return zctas


# ---------------------------------------------------------------------------
# Probe / report
# ---------------------------------------------------------------------------
def run_probe(entity: str = SAMPLE_ZIP) -> None:
    print(f"== Data Commons availability probe for {entity} ==\n")

    # 1) Node identity / geo
    print("-- Node properties (identity + GeoPoint) --")
    try:
        props = fetch_node_props(entity, NODE_PROPERTIES)
        for p in NODE_PROPERTIES:
            mark = "OK " if p in props and props[p] not in (None, [], "") else "MISSING"
            print(f"  [{mark}] {p}: {props.get(p)}")
    except DataCommonsError as e:
        print(f"  ERROR: {e}")
    print()

    # 2) Statistical variables, grouped by target field
    all_candidates = [sv for svs in STATVAR_CANDIDATES.values() for sv in svs]
    try:
        available = fetch_observations(entity, all_candidates)
    except DataCommonsError as e:
        print(f"  ERROR querying observations: {e}")
        return

    print("-- LocationStatistics fields --")
    for field, candidates in STATVAR_CANDIDATES.items():
        if not candidates:
            print(f"\n  {field}:  (no direct Data Commons StatVar — needs another source)")
            continue
        hits = [sv for sv in candidates if sv in available]
        status = "OK" if hits else "MISSING"
        print(f"\n  {field}  [{status}]")
        for sv in candidates:
            if sv in available:
                a = available[sv]
                print(f"    [OK ] {sv} = {a['value']} ({a['date']})")
            else:
                print(f"    [-- ] {sv}")

    # 3) Coverage: can we enumerate all NY ZIPs?
    print("\n-- NY state ZCTA enumeration --")
    try:
        zctas = list_ny_zctas()
        print(f"  containedInPlace returned {len(zctas)} ZCTAs for {NY_STATE_DCID}")
        if zctas:
            print(f"  sample: {zctas[:5]}")
    except DataCommonsError as e:
        print(f"  ERROR: {e}")


def main() -> None:
    entity = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_ZIP
    try:
        run_probe(entity)
    except DataCommonsError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
