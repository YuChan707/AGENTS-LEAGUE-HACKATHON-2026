"""Data processor: convierte la data CRUDA real (Census, por zip_code) en grupos
de audiencia SINTETICOS de comportamiento online, usando un Llama 3B dockerizado.

Pipeline por ubicacion (zip_code):

  1. MODELO ESTADISTICO  (BEHAVIOR_MODEL_PROMPT -> list[BehaviorFormula])
       Variables estadisticas de comportamiento y COMO cambian segun los rasgos:
       genero, edad, income/clase social (low..high), etnia y educacion.

  2. GRUPOS POR CAMPO/TEMA  (FIELD_GROUPS_PROMPT -> list[FieldBehaviorGroup])
       Audiencias orientadas a temas (tecnologia, entretenimiento, educacion,
       salud, finanzas, politica, familia) con su comportamiento caracteristico.

  3. GRUPOS VARIADOS  (prompt AUTOMATIZADO -> GroupBehaviorProfile por combinacion)
       Se enumeran combinaciones diversas de factores y, para cada una, se piden
       los niveles de comportamiento como RANGOS (min/esperado/max) = los SCORES
       de salida de la audiencia.

  4. SPEC CONSOLIDADA + SCORES AGREGADOS  -> se persiste todo por zip_code.

El acceso al modelo (Dapr Conversation API / endpoint OpenAI-compatible / mock)
lo abstrae `llm_client.LlamaClient`; el grounding en evidencia real lo aporta
`foundry_iq.FoundryIQ`. Si no hay modelo disponible, se cae a fixtures validos
para que el pipeline corra siempre.

Uso:
    python -m data_processor                 # procesa lo persistido por el ingestor
    python -m data_processor --limit 3       # solo 3 ubicaciones
    LLM_TRANSPORT=mock python -m data_processor   # sin modelo real (demo/CI)
"""

from __future__ import annotations

import logging

from dtos.data_ingestors import FIELD_DOMAINS, INCOME_BRACKETS

from .foundry_iq import FoundryIQ
from .llm_client import LlamaClient, LLMUnavailable, extract_json
from .persistence import (
    load_locations,
    save_audience_specs,
    save_locations,
    save_processor_output,
)
from .prompts import (
    BEHAVIOR_MODEL_PROMPT,
    FIELD_GROUPS_PROMPT,
    GROUP_PROFILE_PROMPT,
    REACTION_PROMPT,
    PROMPTS,
    PromptSpec,
)

logger = logging.getLogger("DataProcessor")

# Buckets etarios para variar los grupos.
AGE_BUCKETS = ((18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 120))

# Metricas nucleo para los perfiles de grupo (el modelo completo cubre todas;
# para los grupos variados usamos un subset accionable y mas barato de generar).
CORE_METRICS = (
    "adoption_propensity",
    "engagement_likelihood",
    "trust_score",
    "sentiment_score",
    "conversion_rate",
    "sharing_propensity",
)

# Temas principales primero (los que pide el usuario), luego el resto.
_PRIORITY_FIELDS = ("technology", "entertainment", "education", "health")
TOPIC_FIELDS = _PRIORITY_FIELDS + tuple(f for f in FIELD_DOMAINS if f not in _PRIORITY_FIELDS)

_EDU_BY_INCOME = {
    "low": "high_school",
    "lower_middle": "associate",
    "middle": "bachelor",
    "upper_middle": "bachelor",
    "high": "master",
}


# ---------------------------------------------------------------------------
# Generacion validada (mock-aware, con grounding y reintentos)
# ---------------------------------------------------------------------------
def generate(
    spec: PromptSpec,
    *,
    client: LlamaClient,
    foundry: FoundryIQ,
    location_stats: dict | None = None,
    build_args: tuple = (),
    build_kwargs: dict | None = None,
    mock_args: tuple = (),
    mock_kwargs: dict | None = None,
    grounding_query: str = "",
):
    """Ejecuta un PromptSpec end-to-end y devuelve la entidad validada.

    - Inyecta grounding de Foundry IQ.
    - Si el transporte es mock (o el modelo falla), usa el fixture del spec.
    - Valida SIEMPRE contra el marshmallow schema (asi el mock tambien se valida).
    """
    build_kwargs = dict(build_kwargs or {})
    mock_kwargs = dict(mock_kwargs or {})

    grounding = foundry.ground(grounding_query or spec.name, location_stats)
    build_kwargs.setdefault("grounding", grounding)

    raw = None
    if not client.is_mock:
        prompt = spec.build(*build_args, **build_kwargs)
        for attempt in (1, 2):
            try:
                text = client.complete(prompt["system"], prompt["user"])
                raw = extract_json(text)
                return spec.validate(raw)
            except LLMUnavailable as exc:
                logger.warning("LLM no disponible para %s: %s -> uso mock", spec.name, exc)
                raw = None
                break
            except Exception as exc:  # noqa: BLE001 - JSON invalido / validacion
                logger.warning("Salida invalida de %s (intento %d): %s", spec.name, attempt, exc)
                raw = None

    # Camino mock / fallback.
    raw = spec.mock(*mock_args, **mock_kwargs)
    return spec.validate(raw)


# ---------------------------------------------------------------------------
# Prompt AUTOMATIZADO: definiciones de grupos de audiencia variados
# ---------------------------------------------------------------------------
def top_ethnicities(location_stats: dict | None, n: int = 3) -> list[str]:
    dist = (location_stats or {}).get("ethnicity_distribution") or {}
    ranked = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
    eths = [k for k, v in ranked if v and v > 0][:n]
    return eths or ["white", "hispanic", "asian"]


def build_varied_group_definitions(
    location_stats: dict | None,
    *,
    location_id: str | None = None,
    max_groups: int = 12,
) -> list[dict]:
    """Genera, de forma AUTOMATICA, combinaciones diversas de factores.

    Varia genero x income/clase x edad x etnia x campo para cubrir un abanico
    representativo (no el producto cartesiano completo). Las etnias salen de la
    distribucion REAL de la ubicacion.
    """
    genders = ["male", "female", "non_binary"]
    incomes = list(INCOME_BRACKETS)              # low, lower_middle, middle, upper_middle, high
    eths = top_ethnicities(location_stats)
    fields = list(TOPIC_FIELDS)

    definitions: list[dict] = []
    for i in range(max_groups):
        gender = genders[i % len(genders)]
        income = incomes[i % len(incomes)]
        amin, amax = AGE_BUCKETS[i % len(AGE_BUCKETS)]
        eth = eths[i % len(eths)]
        field = fields[i % len(fields)]
        edu = _EDU_BY_INCOME.get(income, "bachelor")
        definition = {
            "group_name": f"{field} {gender} {eth} {amin}-{amax} ({income})",
            "age_range": {"min_age": amin, "max_age": amax},
            "gender": gender,
            "ethnicity": eth,
            "income_bracket": income,
            "education_level": edu,
            "field_domain": field,
        }
        if location_id:
            definition["location_id"] = location_id
        definitions.append(definition)
    return definitions


# ---------------------------------------------------------------------------
# Agregacion de scores (rangos promedio de reaccion)
# ---------------------------------------------------------------------------
def summarize_scores(group_profiles: list[dict]) -> dict:
    """Resume los scores de la audiencia: por metrica, el rango promedio.

    Devuelve {metric: {expected_avg, min, max, n}} a partir de los
    behavior_ranges de todos los grupos. Es la vista de "scores de rangos
    promedio de reacciones" de la ubicacion.
    """
    agg: dict[str, dict] = {}
    for profile in group_profiles:
        for rng in profile.get("behavior_ranges", []):
            metric = rng.get("metric")
            if not metric:
                continue
            bucket = agg.setdefault(metric, {"_expected": [], "min": None, "max": None})
            exp = rng.get("expected_value")
            if exp is None:
                exp = (rng.get("min_value", 0.0) + rng.get("max_value", 0.0)) / 2
            bucket["_expected"].append(exp)
            lo, hi = rng.get("min_value"), rng.get("max_value")
            if lo is not None:
                bucket["min"] = lo if bucket["min"] is None else min(bucket["min"], lo)
            if hi is not None:
                bucket["max"] = hi if bucket["max"] is None else max(bucket["max"], hi)

    summary = {}
    for metric, bucket in agg.items():
        exps = bucket["_expected"]
        summary[metric] = {
            "expected_avg": round(sum(exps) / len(exps), 4) if exps else None,
            "min": round(bucket["min"], 4) if bucket["min"] is not None else None,
            "max": round(bucket["max"], 4) if bucket["max"] is not None else None,
            "n_groups": len(exps),
        }
    return summary


# ---------------------------------------------------------------------------
# Procesar UNA ubicacion
# ---------------------------------------------------------------------------
def _location_view(location: dict) -> tuple[dict, str, str | None]:
    stats = location.get("statistics") or {}
    label = " ".join(str(x) for x in (location.get("city"), location.get("state"), location.get("zip_code")) if x)
    return stats, label, location.get("location_id")


def process_location(
    location: dict,
    *,
    client: LlamaClient,
    foundry: FoundryIQ,
    max_groups: int = 12,
    persist: bool = True,
) -> dict:
    """Genera el set completo de audiencia sintetica para una ubicacion."""
    stats, label, location_id = _location_view(location)
    zip_code = location.get("zip_code") or "unknown"
    logger.info("Procesando %s (zip %s)...", label or zip_code, zip_code)

    # 1) Modelo estadistico de comportamiento.
    behavior_model = generate(
        BEHAVIOR_MODEL_PROMPT,
        client=client,
        foundry=foundry,
        location_stats=stats,
        build_args=(stats,),
        build_kwargs={"location_label": label},
        mock_args=(stats,),
        grounding_query=f"comportamiento digital poblacion {label}",
    )

    # 2) Grupos por campo/tema.
    field_groups = generate(
        FIELD_GROUPS_PROMPT,
        client=client,
        foundry=foundry,
        location_stats=stats,
        build_args=(stats,),
        build_kwargs={"location_label": label},
        mock_args=(stats,),
        grounding_query=f"audiencias por campo {label}",
    )

    # 3) Grupos variados (prompt automatizado) -> perfiles con rangos/scores.
    definitions = build_varied_group_definitions(stats, location_id=location_id, max_groups=max_groups)
    group_profiles = []
    for definition in definitions:
        profile = generate(
            GROUP_PROFILE_PROMPT,
            client=client,
            foundry=foundry,
            location_stats=stats,
            build_args=(definition, stats),
            build_kwargs={"location_label": label, "metrics": CORE_METRICS},
            mock_args=(definition, stats),
            mock_kwargs={"metrics": CORE_METRICS},
            grounding_query=f"{definition['group_name']} {label}",
        )
        group_profiles.append(profile)

    # 4) Spec consolidada + scores agregados.
    spec = {
        "zip_code": zip_code,
        "location_id": location_id,
        "location_label": label,
        "n_field_groups": len(field_groups),
        "n_audience_groups": len(group_profiles),
        "behavior_metrics_modeled": [f.get("metric") for f in behavior_model],
        "topic_fields": [g.get("field_domain") for g in field_groups],
        "audience_scores": summarize_scores(group_profiles),
        "behavior_model": behavior_model,
        "field_groups": field_groups,
        "group_profiles": group_profiles,
    }

    if persist:
        save_processor_output("behavior_model", zip_code, behavior_model)
        save_processor_output("field_groups", zip_code, field_groups)
        save_processor_output("group_profiles", zip_code, group_profiles)
        save_audience_specs(zip_code, spec)
        logger.info(
            "Persistido zip %s: %d field groups, %d audience groups",
            zip_code, len(field_groups), len(group_profiles),
        )
    return spec


# ---------------------------------------------------------------------------
# Entry point del pipeline
# ---------------------------------------------------------------------------
def run(
    *,
    limit: int | None = None,
    max_groups: int = 12,
    transport: str = "",
    persist: bool = True,
) -> list[dict]:
    """Procesa las ubicaciones persistidas por el data_ingestor."""
    client = LlamaClient(transport=transport)
    foundry = FoundryIQ()

    locations = load_locations()
    if not locations:
        logger.warning(
            "No hay ubicaciones persistidas. Corre primero el data_ingestor "
            "(python -m data_ingestor.main) para poblar data_ingestor/data/locations/."
        )
        return []

    if limit:
        locations = locations[:limit]

    logger.info(
        "Transporte LLM=%s | Foundry IQ remoto=%s | %d ubicaciones",
        client.transport, foundry.enabled, len(locations),
    )

    specs = []
    for location in locations:
        try:
            specs.append(process_location(location, client=client, foundry=foundry, max_groups=max_groups, persist=persist))
        except Exception as exc:  # noqa: BLE001 - no abortar todo por una ubicacion
            logger.exception("Fallo procesando %s: %s", location.get("zip_code"), exc)
    logger.info("Pipeline finalizado: %d ubicaciones procesadas.", len(specs))
    return specs


__all__ = [
    "run",
    "process_location",
    "generate",
    "build_varied_group_definitions",
    "summarize_scores",
    "top_ethnicities",
    "LlamaClient",
    "FoundryIQ",
    "PROMPTS",
    "PromptSpec",
    "BEHAVIOR_MODEL_PROMPT",
    "FIELD_GROUPS_PROMPT",
    "GROUP_PROFILE_PROMPT",
    "REACTION_PROMPT",
    "load_locations",
    "save_locations",
    "AGE_BUCKETS",
    "CORE_METRICS",
    "TOPIC_FIELDS",
]
