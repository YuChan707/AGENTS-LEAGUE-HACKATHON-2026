"""Prompts para generar DATA SINTETICA de comportamiento con una LLM.

Genera, a partir de la data CRUDA real de una ubicacion (Location /
LocationStatistics), tres tipos de salida que validan contra los schemas de
`dtos`:

  1) build_behavior_model_prompt -> list[BehaviorFormula]
       Formulas estadisticas reproducibles que dicen COMO cambia cada metrica
       de comportamiento segun factores demograficos (edad, genero, etnia,
       income, educacion).

  2) build_field_groups_prompt -> list[FieldBehaviorGroup]
       Grupos con comportamiento caracteristico por CAMPO (tech, educacion,
       finanzas, politica, entretenimiento, familia), cada uno con su propio
       modelo de comportamiento.

  3) build_reaction_prompt -> ReactionProfile
       Como reacciona un segmento a un PRODUCTO DIGITAL, aplicando las formulas
       del modelo y atribuyendo el resultado a cada factor.

Cada builder devuelve {"model", "system", "user"} listo para enviar a la API de
Claude (Messages API). La LLM debe responder SOLO con el JSON pedido; ese JSON
se valida luego con los marshmallow schemas de `dtos` (.load()).

Modelo recomendado: Claude Opus 4.8 (claude-opus-4-8) por la calidad del
razonamiento estadistico; para volumen alto, Sonnet 4.6 (claude-sonnet-4-6).
"""

from __future__ import annotations

import json
from textwrap import dedent

from dtos.data_ingestors import (
    BEHAVIOR_FACTORS,
    BEHAVIOR_METRICS,
    COMBINATION_RULES,
    EDUCATION_LEVELS,
    EFFECT_TYPES,
    FIELD_DOMAINS,
    GENDERS,
    INCOME_BRACKETS,
)

# Modelo por defecto para la generacion (ver docstring para alternativas).
DEFAULT_MODEL = "claude-opus-4-8"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _enum(values: tuple[str, ...]) -> str:
    return " | ".join(values)


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Guardrails compartidos por todos los prompts
# ---------------------------------------------------------------------------
_GUARDRAILS = dedent(
    f"""
    REGLAS DURAS (no negociables):
    - Responde EXCLUSIVAMENTE con JSON valido. Sin texto antes ni despues, sin
      markdown, sin ```.
    - Todos los scores y probabilidades van en el rango [0, 1] salvo que el
      contrato diga otra cosa. Usa numeros, no strings.
    - Las formulas deben ser REPRODUCIBLES: dado un segmento concreto, aplicar
      la expresion + los modifiers debe dar un numero. No inventes notacion
      ambigua.
    - Ancla cada estimacion en la data REAL provista (median_income, age_ranges,
      ethnicity_distribution, unemployment_rate, etc.). Si infieres, dilo en el
      campo `rationale`.
    - factor SOLO puede ser uno de: {_enum(BEHAVIOR_FACTORS)}.
    - metric SOLO puede ser una de: {_enum(BEHAVIOR_METRICS)}.
    - effect_type SOLO: {_enum(EFFECT_TYPES)}.
    - combination_rule SOLO: {_enum(COMBINATION_RULES)}.
    - segment_value debe ser coherente con su factor:
        age    -> rangos tipo "18-24", "25-34", "65+"
        gender -> {_enum(GENDERS)}
        income -> {_enum(INCOME_BRACKETS)}
        education -> {_enum(EDUCATION_LEVELS)}
        field  -> {_enum(FIELD_DOMAINS)}
        ethnicity -> usa las etiquetas presentes en ethnicity_distribution.
    - ETICA: modela TENDENCIAS estadisticas agregadas, nunca rasgos
      deterministas de una persona. Nada de estereotipos ofensivos; etnia e
      income se tratan como correlaciones poblacionales, con humildad en
      `confidence`. No inventes PII (nombres, emails, direcciones).
    - Marca siempre "generated_by": "llm".
    """
).strip()


# ---------------------------------------------------------------------------
# Contratos JSON (espejo de los marshmallow schemas en dtos/)
# ---------------------------------------------------------------------------
_FACTOR_MODIFIER_CONTRACT = dedent(
    """
    FactorModifier = {
      "factor": <enum BEHAVIOR_FACTORS>,
      "segment_value": <string coherente con el factor>,
      "effect_type": <enum EFFECT_TYPES>,
      "effect_value": <float>,        // 1.35 = +35% (multiplier), +0.12 (additive), 0.7 (absolute)
      "weight": <float 0-1>,          // opcional; usado si combination_rule = weighted_average
      "rationale": <string: por que, anclado en la data>,
      "confidence": <float 0-1>
    }
    """
).strip()

_BEHAVIOR_FORMULA_CONTRACT = dedent(
    """
    BehaviorFormula = {
      "formula_id": <uuid v4 string>,
      "metric": <enum BEHAVIOR_METRICS>,
      "baseline": <float>,            // valor de la poblacion de referencia, antes de modificar
      "combination_rule": <enum COMBINATION_RULES>,
      "modifiers": [ FactorModifier, ... ],   // al menos 3, cubriendo varios factores
      "expression": <string legible y reproducible,
                     ej: "adoption = clamp(base * Π(multipliers) + Σ(additives), 0, 1)">,
      "output_min": <float, default 0.0>,
      "output_max": <float, default 1.0>,
      "sample_size": <int>,           // n sintetico que respalda la estimacion
      "confidence": <float 0-1>,
      "generated_by": "llm"
    }
    """
).strip()

_FIELD_GROUP_CONTRACT = dedent(
    """
    FieldBehaviorGroup = {
      "group_id": <uuid v4 string>,
      "group_name": <string>,
      "field_domain": <enum FIELD_DOMAINS>,
      "description": <string>,
      "typical_age_range": {"min_age": <int>, "max_age": <int>},
      "typical_income_bracket": <enum INCOME_BRACKETS>,
      "dominant_values": [<string>, ...],
      "preferred_platforms": [<string>, ...],
      "content_format_preferences": [<string>, ...],
      "decision_drivers": [<string>, ...],     // que pesa al decidir adoptar
      "objections": [<string>, ...],           // frenos / razones de rechazo
      "jargon_tolerance": <float 0-1>,
      "product_evaluation_criteria": [<string>, ...],  // su lente al juzgar un producto digital
      "behavior_formulas": [ BehaviorFormula, ... ],
      "generated_by": "llm"
    }
    """
).strip()

_GROUP_PROFILE_CONTRACT = dedent(
    """
    MetricRange = {
      "metric": <enum BEHAVIOR_METRICS>,
      "min_value": <float>,          // nivel minimo dentro del grupo
      "max_value": <float>,          // nivel maximo dentro del grupo
      "expected_value": <float>,     // valor central/esperado
      "min_driver": <string: que combinacion de factores lleva al minimo>,
      "max_driver": <string: que combinacion de factores lleva al maximo>,
      "formula_id": <uuid de la BehaviorFormula de la que sale el rango>
    }

    GroupBehaviorProfile = {
      "profile_id": <uuid v4 string>,
      "group_name": <string descriptivo, ej: "Tech male asian 25-44">,
      "age_range": {"min_age": <int>, "max_age": <int>},
      "gender": <enum GENDERS>,
      "ethnicity": <string presente en la data de la ubicacion>,
      "income_bracket": <enum INCOME_BRACKETS>,
      "education_level": <enum EDUCATION_LEVELS>,
      "field_domain": <enum FIELD_DOMAINS>,
      "behavior_ranges": [ MetricRange, ... ],   // una por metrica relevante
      "formulas": [ BehaviorFormula, ... ],      // las que sustentan los rangos
      "confidence": <float 0-1>,
      "generated_by": "llm"
    }
    """
).strip()

_REACTION_CONTRACT = dedent(
    """
    ReactionProfile = {
      "reaction_id": <uuid v4 string>,
      "asset_id": <uuid del asset, copiado del input>,
      "segment_id": <uuid del segmento, copiado del input>,
      "section": <string opcional: seccion/slide/parrafo>,
      "sentiment_score": <float 0-1>,
      "comprehension_score": <float 0-1>,
      "cultural_fit_score": <float 0-1>,
      "engagement_likelihood": <float 0-1>,
      "metric_scores": { <metric de BEHAVIOR_METRICS>: <float 0-1>, ... },
      "factor_attribution": { <factor>: <float, aporte +/- a la reaccion>, ... },
      "applied_formula_ids": [<uuid de las BehaviorFormula usadas>, ...],
      "strengths": [<string>, ...],
      "risks": [<string>, ...],
      "recommendations": [<string>, ...],
      "confidence": <float 0-1>,
      "generated_by": "llm"
    }
    """
).strip()


# ===========================================================================
# 1) MODELO ESTADISTICO DE COMPORTAMIENTO  ->  list[BehaviorFormula]
# ===========================================================================
BEHAVIOR_MODEL_SYSTEM = dedent(
    f"""
    Eres un cientifico de datos de comportamiento del consumidor digital.
    Tu trabajo: a partir de la estadistica REAL de una ubicacion (censo),
    construir un modelo estadistico que prediga como se comporta su poblacion
    frente a un producto digital, y COMO cambia ese comportamiento segun los
    factores demograficos.

    Entregas un conjunto de BehaviorFormula: una por metrica relevante. Cada
    formula tiene una baseline (la poblacion de referencia) y una lista de
    FactorModifier que ajustan esa baseline segun edad, genero, etnia, income y
    educacion. La expresion debe permitir CALCULAR el valor para cualquier
    segmento.

    {_GUARDRAILS}

    CONTRATOS:
    {_FACTOR_MODIFIER_CONTRACT}

    {_BEHAVIOR_FORMULA_CONTRACT}

    SALIDA: un array JSON de BehaviorFormula. Nada mas.
    """
).strip()


def build_behavior_model_prompt(
    location_stats: dict,
    *,
    location_label: str = "",
    metrics: tuple[str, ...] | None = None,
) -> dict:
    """Prompt para generar el modelo estadistico (list[BehaviorFormula]).

    location_stats: dict de LocationStatistics (median_income, age_ranges,
        ethnicity_distribution, unemployment_rate, poverty_rate, ...).
    metrics: subconjunto de BEHAVIOR_METRICS a modelar (default: todas).
    """
    metrics = metrics or BEHAVIOR_METRICS
    user = dedent(
        f"""
        UBICACION: {location_label or "(sin nombre)"}

        DATA REAL DE LA UBICACION (anclar todo aqui):
        {_json(location_stats)}

        TAREA:
        Genera UNA BehaviorFormula por cada una de estas metricas:
        {_enum(metrics)}

        Para cada formula:
        - Fija una baseline realista para esta ubicacion (usa la data: p. ej. un
          income mediano alto baja price_sensitivity; desempleo alto sube
          churn_risk).
        - Incluye al menos 3 FactorModifier cubriendo factores distintos
          (mezcla age, gender, ethnicity, income, education).
        - Usa los valores reales: si ethnicity_distribution trae "hispanic" y
          "white", los segment_value de etnia deben ser esos.
        - Escribe una expression reproducible y coherente con combination_rule.

        Devuelve SOLO el array JSON de BehaviorFormula.
        """
    ).strip()
    return {"model": DEFAULT_MODEL, "system": BEHAVIOR_MODEL_SYSTEM, "user": user}


# ===========================================================================
# 2) GRUPOS POR CAMPO  ->  list[FieldBehaviorGroup]
# ===========================================================================
FIELD_GROUPS_SYSTEM = dedent(
    f"""
    Eres un estratega de audiencias. Construyes grupos sinteticos con
    comportamiento CARACTERISTICO de un campo profesional/de interes (tech,
    educacion, finanzas, politica, entretenimiento, familia), enfocados a como
    evaluan y adoptan un producto digital.

    Cada grupo es un FieldBehaviorGroup e incluye su PROPIO modelo de
    comportamiento (behavior_formulas), porque cada campo reacciona distinto:
    p. ej. finanzas pesa privacidad/ROI y tiene baja jargon_tolerance al riesgo;
    entretenimiento pesa novedad y tiene alta sharing_propensity.

    {_GUARDRAILS}

    CONTRATOS:
    {_FACTOR_MODIFIER_CONTRACT}

    {_BEHAVIOR_FORMULA_CONTRACT}

    {_FIELD_GROUP_CONTRACT}

    SALIDA: un array JSON de FieldBehaviorGroup. Nada mas.
    """
).strip()


def build_field_groups_prompt(
    location_stats: dict,
    *,
    location_label: str = "",
    domains: tuple[str, ...] = FIELD_DOMAINS,
) -> dict:
    """Prompt para generar un FieldBehaviorGroup por cada dominio de FIELD_DOMAINS."""
    user = dedent(
        f"""
        UBICACION: {location_label or "(sin nombre)"}

        DATA REAL DE LA UBICACION (para calibrar los grupos a la poblacion local):
        {_json(location_stats)}

        TAREA:
        Genera UN FieldBehaviorGroup por cada uno de estos campos:
        {_enum(domains)}

        Para cada grupo:
        - Aterriza el perfil a la poblacion local (usa income/edad reales para
          typical_income_bracket y typical_age_range).
        - product_evaluation_criteria debe reflejar la lente del campo
          (finanzas: ROI/seguridad; familia: facilidad/seguridad de menores;
          tech: extensibilidad/rendimiento; etc.).
        - Incluye 2-4 behavior_formulas por grupo, priorizando
          adoption_propensity, trust_score y engagement_likelihood.

        Devuelve SOLO el array JSON de FieldBehaviorGroup.
        """
    ).strip()
    return {"model": DEFAULT_MODEL, "system": FIELD_GROUPS_SYSTEM, "user": user}


# ===========================================================================
# 3) PERFIL DE GRUPO POR RANGOS  ->  GroupBehaviorProfile
#    Un grupo definido por la COMBINACION de factores (edad+etnia+genero+campo)
#    y como varian sus niveles de comportamiento entre min y max.
# ===========================================================================
GROUP_PROFILE_SYSTEM = dedent(
    f"""
    Eres un cientifico de datos de audiencias. Recibes la definicion de un grupo
    como una COMBINACION de factores (un rango de edad, una etnia concreta, un
    genero, un income, un campo profesional) y la data real de su ubicacion.

    Construyes un GroupBehaviorProfile: para cada metrica de comportamiento das
    un RANGO (min, max, esperado), porque dentro del grupo los niveles VARIAN
    segun donde caiga cada persona en los factores. Tambien entregas las
    BehaviorFormula que sustentan esos rangos, de modo que el rango sea el
    resultado de EVALUAR la formula en los extremos del abanico de factores del
    grupo (no un numero inventado).

    Importante sobre los rangos:
    - min_value = la formula evaluada en la combinacion menos favorable del grupo.
    - max_value = la formula evaluada en la combinacion mas favorable.
    - expected_value = el valor tipico (centro del grupo).
    - min_driver / max_driver: explica que combinacion empuja a cada extremo.

    {_GUARDRAILS}

    CONTRATOS:
    {_FACTOR_MODIFIER_CONTRACT}

    {_BEHAVIOR_FORMULA_CONTRACT}

    {_GROUP_PROFILE_CONTRACT}

    SALIDA: un unico objeto JSON GroupBehaviorProfile. Nada mas.
    """
).strip()


def build_group_profile_prompt(
    group_definition: dict,
    location_stats: dict,
    *,
    location_label: str = "",
    metrics: tuple[str, ...] | None = None,
) -> dict:
    """Prompt para generar un GroupBehaviorProfile (niveles por rango min/max).

    group_definition: combinacion de factores del grupo, ej:
        {"age_range": {"min_age": 25, "max_age": 44}, "gender": "male",
         "ethnicity": "asian", "income_bracket": "upper_middle",
         "education_level": "bachelor", "field_domain": "technology"}
    location_stats: dict de LocationStatistics para anclar las estimaciones.
    """
    metrics = metrics or BEHAVIOR_METRICS
    user = dedent(
        f"""
        UBICACION: {location_label or "(sin nombre)"}

        DEFINICION DEL GRUPO (combinacion de factores):
        {_json(group_definition)}

        DATA REAL DE LA UBICACION (para anclar):
        {_json(location_stats)}

        TAREA:
        1. Genera las BehaviorFormula necesarias (baseline + modifiers por
           factor) para estas metricas: {_enum(metrics)}.
        2. Para cada metrica, calcula un MetricRange evaluando la formula en los
           extremos del grupo: el min en la sub-combinacion menos favorable y el
           max en la mas favorable, con su expected_value y los drivers.
        3. Ensambla un unico GroupBehaviorProfile con la definicion del grupo,
           los behavior_ranges y las formulas que los sustentan.

        Devuelve SOLO el objeto JSON GroupBehaviorProfile.
        """
    ).strip()
    return {"model": DEFAULT_MODEL, "system": GROUP_PROFILE_SYSTEM, "user": user}


# ===========================================================================
# 4) REACCION A UN PRODUCTO DIGITAL  ->  ReactionProfile
# ===========================================================================
REACTION_SYSTEM = dedent(
    f"""
    Eres un panel de investigacion de usuarios sintetico. Recibes (a) un asset
    de producto digital, (b) un segmento de audiencia y (c) el modelo de
    comportamiento (behavior_formulas) que aplica a ese segmento. Simulas como
    reacciona el segmento y CALCULAS las metricas aplicando las formulas.

    No improvises los numeros: parte de las formulas provistas, aplica los
    modifiers que correspondan al segmento y reporta el resultado. En
    factor_attribution explica cuanto empujo cada factor (positivo o negativo).

    {_GUARDRAILS}

    CONTRATO:
    {_REACTION_CONTRACT}

    SALIDA: un unico objeto JSON ReactionProfile. Nada mas.
    """
).strip()


def build_reaction_prompt(
    asset: dict,
    segment: dict,
    behavior_formulas: list[dict],
    *,
    section: str | None = None,
) -> dict:
    """Prompt para generar el ReactionProfile de un segmento ante un asset.

    asset: dict ProjectAsset (asset_id, name, asset_type, summary, language...).
    segment: dict con el perfil demografico+psico+conducta del segmento
        (incluye segment_id y los valores de factores: age, gender, ethnicity,
        income, field...).
    behavior_formulas: list[BehaviorFormula] aplicables al segmento.
    """
    seccion = f'\nSECCION especifica a evaluar: "{section}"' if section else ""
    user = dedent(
        f"""
        ASSET (producto digital a evaluar):
        {_json(asset)}

        SEGMENTO (a quien evaluas):
        {_json(segment)}

        MODELO DE COMPORTAMIENTO APLICABLE (usa estas formulas para calcular):
        {_json(behavior_formulas)}
        {seccion}

        TAREA:
        1. Para cada metrica con formula, aplica baseline + los modifiers que
           matcheen los factores del segmento, respetando combination_rule y el
           clamp de la expresion. Pon el resultado en metric_scores.
        2. Rellena sentiment/comprehension/cultural_fit/engagement coherentes
           con metric_scores.
        3. En factor_attribution reporta el aporte neto de cada factor.
        4. En applied_formula_ids lista los formula_id que usaste.
        5. Da strengths, risks y recommendations accionables para mejorar el
           producto para ESTE segmento.

        Copia asset_id y segment_id del input. Devuelve SOLO el objeto JSON
        ReactionProfile.
        """
    ).strip()
    return {"model": DEFAULT_MODEL, "system": REACTION_SYSTEM, "user": user}


__all__ = [
    "DEFAULT_MODEL",
    "BEHAVIOR_MODEL_SYSTEM",
    "FIELD_GROUPS_SYSTEM",
    "REACTION_SYSTEM",
    "build_behavior_model_prompt",
    "build_field_groups_prompt",
    "build_reaction_prompt",
]
