"""Prompts para generar DATA SINTETICA de comportamiento con el Llama 3B.

Cada prompt se guarda como una ENTIDAD (`PromptSpec`) con sus features:

  * details            -> que hace el prompt / para que sirve.
  * description_input   -> que entrada espera (forma de los argumentos).
  * expected_output     -> contrato de la salida (forma del JSON exigido).
  * output_schema       -> marshmallow Schema con el que se VALIDA la salida.
  * output_is_list      -> si la salida es un array de entidades o una sola.
  * builder             -> arma {"model","system","user"} para el modelo.
  * mock                -> fixture valido (corre el pipeline sin modelo real).

Asi garantizamos que lo que devuelve la LLM cumple los requisitos para crear
las entidades de grupos estadisticos: `expected_output` documenta el contrato y
`output_schema` lo hace cumplir via `.load()`.

A partir de la data CRUDA real de una ubicacion (Location / LocationStatistics)
se generan cuatro tipos de salida:

  1) BEHAVIOR_MODEL_PROMPT  -> list[BehaviorFormula]
       Formulas estadisticas reproducibles: COMO cambia cada metrica de
       comportamiento segun genero, edad, etnia, income/clase y educacion.

  2) FIELD_GROUPS_PROMPT    -> list[FieldBehaviorGroup]
       Grupos por CAMPO/tema (tech, educacion, entretenimiento, salud,
       finanzas, politica, familia), cada uno con su modelo de comportamiento.

  3) GROUP_PROFILE_PROMPT   -> GroupBehaviorProfile
       Un grupo definido por COMBINACION de factores y sus niveles como RANGOS
       (min / esperado / max) -> los "scores de rangos promedio de reaccion".

  4) REACTION_PROMPT        -> ReactionProfile
       Como reacciona un segmento a un PRODUCTO DIGITAL, con scores y atribucion.

El modelo por defecto es el LLAMA dockerizado (LLAMA_MODEL en el entorno),
servido via Dapr Conversation API o endpoint OpenAI-compatible (ver llm_client).
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable
from dataclasses import dataclass
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
    BehaviorFormula as BehaviorFormulaSchema,
    FieldBehaviorGroup as FieldBehaviorGroupSchema,
    GroupBehaviorProfile as GroupBehaviorProfileSchema,
)
from dtos.data_processors import ReactionProfile as ReactionProfileSchema

# Modelo por defecto: el Llama dockerizado (override con LLAMA_MODEL).
DEFAULT_MODEL = os.getenv("LLAMA_MODEL", "llama3.2:3b")


# ---------------------------------------------------------------------------
# Entidad de prompt
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PromptSpec:
    """Un prompt como entidad, con contrato de entrada/salida y validador."""

    name: str
    details: str
    description_input: str
    expected_output: str
    builder: Callable[..., dict]
    output_schema: type
    output_is_list: bool
    mock: Callable[..., object]
    model: str = DEFAULT_MODEL

    def build(self, *args, **kwargs) -> dict:
        """Devuelve {"model","system","user"} listo para el cliente LLM."""
        return self.builder(*args, **kwargs)

    def validate(self, data):
        """Valida la salida de la LLM contra el schema. Devuelve la entidad."""
        schema = self.output_schema()
        return schema.load(data, many=self.output_is_list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _enum(values: tuple[str, ...]) -> str:
    return " | ".join(values)


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _with_grounding(user: str, grounding: str = "") -> str:
    """Anexa el bloque de evidencia de Foundry IQ al mensaje de usuario."""
    if not grounding:
        return user
    return f"{grounding}\n\n{user}"


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
        income -> {_enum(INCOME_BRACKETS)}   (clase social: low=baja ... high=alta)
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
                     ej: "adoption = clamp(base * P(multipliers) + S(additives), 0, 1)">,
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
    grounding: str = "",
) -> dict:
    """Prompt para generar el modelo estadistico (list[BehaviorFormula])."""
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
    return {"model": DEFAULT_MODEL, "system": BEHAVIOR_MODEL_SYSTEM, "user": _with_grounding(user, grounding)}


# ===========================================================================
# 2) GRUPOS POR CAMPO / TEMA  ->  list[FieldBehaviorGroup]
# ===========================================================================
FIELD_GROUPS_SYSTEM = dedent(
    f"""
    Eres un estratega de audiencias. Construyes grupos sinteticos con
    comportamiento CARACTERISTICO de un campo/tema (tecnologia, educacion,
    entretenimiento, salud, finanzas, politica, familia), enfocados a como
    evaluan y adoptan un producto digital. Son los representantes que usa el
    usuario cuando quiere la reaccion de un publico orientado a un campo.

    Cada grupo es un FieldBehaviorGroup e incluye su PROPIO modelo de
    comportamiento (behavior_formulas), porque cada campo reacciona distinto:
    p. ej. salud pesa privacidad/evidencia y tiene baja tolerancia al riesgo;
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
    grounding: str = "",
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
          (salud: privacidad/evidencia clinica; finanzas: ROI/seguridad;
          tech: extensibilidad/rendimiento; entretenimiento: novedad; etc.).
        - Incluye 2-4 behavior_formulas por grupo, priorizando
          adoption_propensity, trust_score y engagement_likelihood.

        Devuelve SOLO el array JSON de FieldBehaviorGroup.
        """
    ).strip()
    return {"model": DEFAULT_MODEL, "system": FIELD_GROUPS_SYSTEM, "user": _with_grounding(user, grounding)}


# ===========================================================================
# 3) PERFIL DE GRUPO POR RANGOS  ->  GroupBehaviorProfile
# ===========================================================================
GROUP_PROFILE_SYSTEM = dedent(
    f"""
    Eres un cientifico de datos de audiencias. Recibes la definicion de un grupo
    como una COMBINACION de factores (un rango de edad, una etnia concreta, un
    genero, un income/clase social, un campo) y la data real de su ubicacion.

    Construyes un GroupBehaviorProfile: para cada metrica de comportamiento das
    un RANGO (min, max, esperado), porque dentro del grupo los niveles VARIAN
    segun donde caiga cada persona en los factores. Tambien entregas las
    BehaviorFormula que sustentan esos rangos, de modo que el rango sea el
    resultado de EVALUAR la formula en los extremos del abanico de factores del
    grupo (no un numero inventado).

    Importante sobre los rangos (son los "scores" de salida de la audiencia):
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
    grounding: str = "",
) -> dict:
    """Prompt para generar un GroupBehaviorProfile (niveles por rango min/max)."""
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
    return {"model": DEFAULT_MODEL, "system": GROUP_PROFILE_SYSTEM, "user": _with_grounding(user, grounding)}


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
    grounding: str = "",
) -> dict:
    """Prompt para generar el ReactionProfile de un segmento ante un asset."""
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
    return {"model": DEFAULT_MODEL, "system": REACTION_SYSTEM, "user": _with_grounding(user, grounding)}


# ===========================================================================
# MOCKS: fixtures validos para correr el pipeline sin modelo real (demo/CI).
# ===========================================================================
def _uuid() -> str:
    return str(uuid.uuid4())


def _mock_modifiers() -> list[dict]:
    return [
        {
            "factor": "income",
            "segment_value": "high",
            "effect_type": "multiplier",
            "effect_value": 1.2,
            "weight": 0.4,
            "rationale": "Mayor income reduce friccion de adopcion (mock).",
            "confidence": 0.6,
        },
        {
            "factor": "age",
            "segment_value": "25-34",
            "effect_type": "multiplier",
            "effect_value": 1.15,
            "weight": 0.3,
            "rationale": "Adultos jovenes adoptan mas rapido (mock).",
            "confidence": 0.6,
        },
        {
            "factor": "education",
            "segment_value": "bachelor",
            "effect_type": "additive",
            "effect_value": 0.05,
            "weight": 0.3,
            "rationale": "Mayor educacion sube comprension (mock).",
            "confidence": 0.55,
        },
    ]


def _mock_formula(metric: str) -> dict:
    return {
        "formula_id": _uuid(),
        "metric": metric,
        "baseline": 0.5,
        "combination_rule": "multiplicative",
        "modifiers": _mock_modifiers(),
        "expression": f"{metric} = clamp(base * P(mult) + S(add), 0, 1)",
        "output_min": 0.0,
        "output_max": 1.0,
        "sample_size": 1000,
        "confidence": 0.6,
        "generated_by": "llm",
    }


def mock_behavior_model(location_stats=None, *, metrics=None, **_kw) -> list[dict]:
    metrics = metrics or BEHAVIOR_METRICS
    return [_mock_formula(m) for m in metrics]


def mock_field_groups(location_stats=None, *, domains=FIELD_DOMAINS, **_kw) -> list[dict]:
    out = []
    for d in domains:
        out.append(
            {
                "group_id": _uuid(),
                "group_name": f"{d.title()} audience (mock)",
                "field_domain": d,
                "description": f"Grupo sintetico orientado al campo {d} (mock fixture).",
                "typical_age_range": {"min_age": 25, "max_age": 44},
                "typical_income_bracket": "middle",
                "dominant_values": ["calidad", "confianza"],
                "preferred_platforms": ["instagram", "youtube"],
                "content_format_preferences": ["video", "articulo"],
                "decision_drivers": ["utilidad", "precio"],
                "objections": ["privacidad", "curva de aprendizaje"],
                "jargon_tolerance": 0.5,
                "product_evaluation_criteria": ["usabilidad", "confianza"],
                "behavior_formulas": [
                    _mock_formula("adoption_propensity"),
                    _mock_formula("trust_score"),
                ],
                "generated_by": "llm",
            }
        )
    return out


def mock_group_profile(group_definition=None, location_stats=None, *, metrics=None, **_kw) -> dict:
    metrics = metrics or BEHAVIOR_METRICS
    gd = group_definition or {}
    formulas = [_mock_formula(m) for m in metrics]
    ranges = [
        {
            "metric": f["metric"],
            "min_value": 0.35,
            "max_value": 0.75,
            "expected_value": 0.55,
            "min_driver": "combinacion menos favorable del grupo (mock)",
            "max_driver": "combinacion mas favorable del grupo (mock)",
            "formula_id": f["formula_id"],
        }
        for f in formulas
    ]
    profile = {
        "profile_id": _uuid(),
        "group_name": gd.get("group_name") or "Mock group profile",
        "behavior_ranges": ranges,
        "formulas": formulas,
        "confidence": 0.6,
        "generated_by": "llm",
    }
    for key in ("age_range", "gender", "ethnicity", "income_bracket", "education_level", "field_domain", "location_id"):
        if gd.get(key) is not None:
            profile[key] = gd[key]
    return profile


def mock_reaction(asset=None, segment=None, behavior_formulas=None, *, section=None, **_kw) -> dict:
    asset = asset or {}
    segment = segment or {}
    return {
        "reaction_id": _uuid(),
        "asset_id": asset.get("asset_id") or _uuid(),
        "segment_id": segment.get("segment_id") or _uuid(),
        "section": section,
        "sentiment_score": 0.6,
        "comprehension_score": 0.65,
        "cultural_fit_score": 0.6,
        "engagement_likelihood": 0.55,
        "metric_scores": {"adoption_propensity": 0.58, "trust_score": 0.6},
        "factor_attribution": {"income": 0.1, "age": 0.05},
        "applied_formula_ids": [f["formula_id"] for f in (behavior_formulas or []) if isinstance(f, dict) and f.get("formula_id")],
        "strengths": ["Propuesta clara (mock)"],
        "risks": ["Falta prueba social (mock)"],
        "recommendations": ["Agregar testimonios (mock)"],
        "confidence": 0.6,
        "generated_by": "llm",
    }


# ===========================================================================
# REGISTRO DE PROMPTS (entidades)
# ===========================================================================
BEHAVIOR_MODEL_PROMPT = PromptSpec(
    name="behavior_model",
    details=(
        "Construye el modelo estadistico de comportamiento de una ubicacion: "
        "una formula reproducible por metrica que dice COMO cambia el "
        "comportamiento segun genero, edad, etnia, income/clase y educacion."
    ),
    description_input=(
        "location_stats (dict LocationStatistics: median_income, age_ranges, "
        "ethnicity_distribution, unemployment_rate, poverty_rate, ...), "
        "location_label opcional, metrics opcional (subset de BEHAVIOR_METRICS), "
        "grounding opcional (evidencia de Foundry IQ)."
    ),
    expected_output="Array JSON de BehaviorFormula (>=1 por metrica pedida).",
    builder=build_behavior_model_prompt,
    output_schema=BehaviorFormulaSchema,
    output_is_list=True,
    mock=mock_behavior_model,
)

FIELD_GROUPS_PROMPT = PromptSpec(
    name="field_groups",
    details=(
        "Genera grupos de audiencia orientados a un campo/tema (tecnologia, "
        "educacion, entretenimiento, salud, finanzas, politica, familia), cada "
        "uno con su comportamiento caracteristico y su propio modelo."
    ),
    description_input=(
        "location_stats (dict), location_label opcional, domains opcional "
        "(subset de FIELD_DOMAINS), grounding opcional."
    ),
    expected_output="Array JSON de FieldBehaviorGroup (uno por dominio pedido).",
    builder=build_field_groups_prompt,
    output_schema=FieldBehaviorGroupSchema,
    output_is_list=True,
    mock=mock_field_groups,
)

GROUP_PROFILE_PROMPT = PromptSpec(
    name="group_profile",
    details=(
        "Genera el perfil de un grupo definido por COMBINACION de factores "
        "(edad+genero+etnia+income+campo) con sus niveles de comportamiento "
        "como RANGOS (min/esperado/max): los scores de salida de la audiencia."
    ),
    description_input=(
        "group_definition (dict con age_range, gender, ethnicity, "
        "income_bracket, education_level, field_domain), location_stats (dict), "
        "location_label opcional, metrics opcional, grounding opcional."
    ),
    expected_output="Objeto JSON GroupBehaviorProfile con behavior_ranges y formulas.",
    builder=build_group_profile_prompt,
    output_schema=GroupBehaviorProfileSchema,
    output_is_list=False,
    mock=mock_group_profile,
)

REACTION_PROMPT = PromptSpec(
    name="reaction",
    details=(
        "Simula la reaccion de un segmento ante un producto digital aplicando "
        "el modelo de comportamiento; devuelve scores y atribucion por factor."
    ),
    description_input=(
        "asset (dict ProjectAsset), segment (dict del segmento), "
        "behavior_formulas (list[BehaviorFormula]), section opcional, grounding opcional."
    ),
    expected_output="Objeto JSON ReactionProfile con scores 0-1, atribucion y feedback.",
    builder=build_reaction_prompt,
    output_schema=ReactionProfileSchema,
    output_is_list=False,
    mock=mock_reaction,
)

# Registro accesible por nombre.
PROMPTS: dict[str, PromptSpec] = {
    p.name: p
    for p in (BEHAVIOR_MODEL_PROMPT, FIELD_GROUPS_PROMPT, GROUP_PROFILE_PROMPT, REACTION_PROMPT)
}


__all__ = [
    "DEFAULT_MODEL",
    "PromptSpec",
    "PROMPTS",
    "BEHAVIOR_MODEL_PROMPT",
    "FIELD_GROUPS_PROMPT",
    "GROUP_PROFILE_PROMPT",
    "REACTION_PROMPT",
    "BEHAVIOR_MODEL_SYSTEM",
    "FIELD_GROUPS_SYSTEM",
    "GROUP_PROFILE_SYSTEM",
    "REACTION_SYSTEM",
    "build_behavior_model_prompt",
    "build_field_groups_prompt",
    "build_group_profile_prompt",
    "build_reaction_prompt",
]
