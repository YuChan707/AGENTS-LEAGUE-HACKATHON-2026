"""Prompts to generate SYNTHETIC behavior DATA with the Llama 3B.

Each prompt is stored as an ENTITY (`PromptSpec`) with its features:

  * details            -> what the prompt does / what it is for.
  * description_input   -> what input it expects (shape of the arguments).
  * expected_output     -> output contract (shape of the required JSON).
  * output_schema       -> marshmallow Schema used to VALIDATE the output.
  * output_is_list      -> whether the output is an array of entities or a single one.
  * builder             -> assembles {"model","system","user"} for the model.
  * mock                -> valid fixture (runs the pipeline without a real model).

This way we guarantee that what the LLM returns meets the requirements to create
the statistical group entities: `expected_output` documents the contract and
`output_schema` enforces it via `.load()`.

From the real RAW data of a location (Location / LocationStatistics)
four types of output are generated:

  1) BEHAVIOR_MODEL_PROMPT  -> list[BehaviorFormula]
       Reproducible statistical formulas: HOW each behavior metric
       changes according to gender, age, ethnicity, income/class and education.

  2) FIELD_GROUPS_PROMPT    -> list[FieldBehaviorGroup]
       Groups by FIELD/topic (tech, education, entertainment, health,
       finance, politics, family), each with its own behavior model.

  3) GROUP_PROFILE_PROMPT   -> GroupBehaviorProfile
       A group defined by a COMBINATION of factors and its levels as RANGES
       (min / expected / max) -> the "average reaction range scores".

  4) REACTION_PROMPT        -> ReactionProfile
       How a segment reacts to a DIGITAL PRODUCT, with scores and attribution.

The default model is the dockerized LLAMA (LLAMA_MODEL in the environment),
served via Dapr Conversation API or an OpenAI-compatible endpoint (see llm_client).
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

# Default model: the dockerized Llama (override with LLAMA_MODEL).
DEFAULT_MODEL = os.getenv("LLAMA_MODEL", "llama3.2:3b")


# ---------------------------------------------------------------------------
# Prompt entity
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PromptSpec:
    """A prompt as an entity, with input/output contract and validator."""

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
        """Returns {"model","system","user"} ready for the LLM client."""
        return self.builder(*args, **kwargs)

    def validate(self, data):
        """Validates the LLM output against the schema. Returns the entity."""
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
    """Appends the Foundry IQ evidence block to the user message."""
    if not grounding:
        return user
    return f"{grounding}\n\n{user}"


# ---------------------------------------------------------------------------
# Guardrails shared by all prompts
# ---------------------------------------------------------------------------
_GUARDRAILS = dedent(
    f"""
    HARD RULES (non-negotiable):
    - Respond EXCLUSIVELY with valid JSON. No text before or after, no
      markdown, no ```.
    - All scores and probabilities go in the range [0, 1] unless the
      contract says otherwise. Use numbers, not strings.
    - Formulas must be REPRODUCIBLE: given a concrete segment, applying
      the expression + the modifiers must yield a number. Do not invent
      ambiguous notation.
    - Anchor every estimate in the REAL data provided (median_income, age_ranges,
      ethnicity_distribution, unemployment_rate, etc.). If you infer, say so in the
      `rationale` field.
    - factor can ONLY be one of: {_enum(BEHAVIOR_FACTORS)}.
    - metric can ONLY be one of: {_enum(BEHAVIOR_METRICS)}.
    - effect_type ONLY: {_enum(EFFECT_TYPES)}.
    - combination_rule ONLY: {_enum(COMBINATION_RULES)}.
    - segment_value must be coherent with its factor:
        age    -> ranges like "18-24", "25-34", "65+"
        gender -> {_enum(GENDERS)}
        income -> {_enum(INCOME_BRACKETS)}   (social class: low=lowest ... high=highest)
        education -> {_enum(EDUCATION_LEVELS)}
        field  -> {_enum(FIELD_DOMAINS)}
        ethnicity -> use the labels present in ethnicity_distribution.
    - ETHICS: model aggregated statistical TRENDS, never deterministic
      traits of an individual. No offensive stereotypes; ethnicity and
      income are treated as population correlations, with humility in
      `confidence`. Do not invent PII (names, emails, addresses).
    - Always mark "generated_by": "llm".
    """
).strip()


# ---------------------------------------------------------------------------
# JSON contracts (mirror of the marshmallow schemas in dtos/)
# ---------------------------------------------------------------------------
_FACTOR_MODIFIER_CONTRACT = dedent(
    """
    FactorModifier = {
      "factor": <enum BEHAVIOR_FACTORS>,
      "segment_value": <string coherent with the factor>,
      "effect_type": <enum EFFECT_TYPES>,
      "effect_value": <float>,        // 1.35 = +35% (multiplier), +0.12 (additive), 0.7 (absolute)
      "weight": <float 0-1>,          // optional; used if combination_rule = weighted_average
      "rationale": <string: why, anchored in the data>,
      "confidence": <float 0-1>
    }
    """
).strip()

_BEHAVIOR_FORMULA_CONTRACT = dedent(
    """
    BehaviorFormula = {
      "formula_id": <uuid v4 string>,
      "metric": <enum BEHAVIOR_METRICS>,
      "baseline": <float>,            // reference population value, before modifying
      "combination_rule": <enum COMBINATION_RULES>,
      "modifiers": [ FactorModifier, ... ],   // at least 3, covering several factors
      "expression": <readable and reproducible string,
                     e.g.: "adoption = clamp(base * P(multipliers) + S(additives), 0, 1)">,
      "output_min": <float, default 0.0>,
      "output_max": <float, default 1.0>,
      "sample_size": <int>,           // synthetic n that backs the estimate
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
      "decision_drivers": [<string>, ...],     // what weighs when deciding to adopt
      "objections": [<string>, ...],           // brakes / reasons for rejection
      "jargon_tolerance": <float 0-1>,
      "product_evaluation_criteria": [<string>, ...],  // their lens when judging a digital product
      "behavior_formulas": [ BehaviorFormula, ... ],
      "generated_by": "llm"
    }
    """
).strip()

_GROUP_PROFILE_CONTRACT = dedent(
    """
    MetricRange = {
      "metric": <enum BEHAVIOR_METRICS>,
      "min_value": <float>,          // minimum level within the group
      "max_value": <float>,          // maximum level within the group
      "expected_value": <float>,     // central/expected value
      "min_driver": <string: which combination of factors leads to the minimum>,
      "max_driver": <string: which combination of factors leads to the maximum>,
      "formula_id": <uuid of the BehaviorFormula from which the range comes>
    }

    GroupBehaviorProfile = {
      "profile_id": <uuid v4 string>,
      "group_name": <descriptive string, e.g.: "Tech male asian 25-44">,
      "age_range": {"min_age": <int>, "max_age": <int>},
      "gender": <enum GENDERS>,
      "ethnicity": <string present in the location data>,
      "income_bracket": <enum INCOME_BRACKETS>,
      "education_level": <enum EDUCATION_LEVELS>,
      "field_domain": <enum FIELD_DOMAINS>,
      "behavior_ranges": [ MetricRange, ... ],   // one per relevant metric
      "formulas": [ BehaviorFormula, ... ],      // the ones that back the ranges
      "confidence": <float 0-1>,
      "generated_by": "llm"
    }
    """
).strip()

_REACTION_CONTRACT = dedent(
    """
    ReactionProfile = {
      "reaction_id": <uuid v4 string>,
      "asset_id": <uuid of the asset, copied from the input>,
      "segment_id": <uuid of the segment, copied from the input>,
      "section": <optional string: section/slide/paragraph>,
      "sentiment_score": <float 0-1>,
      "comprehension_score": <float 0-1>,
      "cultural_fit_score": <float 0-1>,
      "engagement_likelihood": <float 0-1>,
      "metric_scores": { <metric from BEHAVIOR_METRICS>: <float 0-1>, ... },
      "factor_attribution": { <factor>: <float, +/- contribution to the reaction>, ... },
      "applied_formula_ids": [<uuid of the BehaviorFormula used>, ...],
      "strengths": [<string>, ...],
      "risks": [<string>, ...],
      "recommendations": [<string>, ...],
      "confidence": <float 0-1>,
      "generated_by": "llm"
    }
    """
).strip()


# ===========================================================================
# 1) STATISTICAL BEHAVIOR MODEL  ->  list[BehaviorFormula]
# ===========================================================================
BEHAVIOR_MODEL_SYSTEM = dedent(
    f"""
    You are a data scientist of digital consumer behavior.
    Your job: from the REAL statistics of a location (census),
    build a statistical model that predicts how its population behaves
    toward a digital product, and HOW that behavior changes according to
    the demographic factors.

    You deliver a set of BehaviorFormula: one per relevant metric. Each
    formula has a baseline (the reference population) and a list of
    FactorModifier that adjust that baseline according to age, gender, ethnicity, income and
    education. The expression must allow CALCULATING the value for any
    segment.

    {_GUARDRAILS}

    CONTRACTS:
    {_FACTOR_MODIFIER_CONTRACT}

    {_BEHAVIOR_FORMULA_CONTRACT}

    OUTPUT: a JSON array of BehaviorFormula. Nothing else.
    """
).strip()


def build_behavior_model_prompt(
    location_stats: dict,
    *,
    location_label: str = "",
    metrics: tuple[str, ...] | None = None,
    grounding: str = "",
) -> dict:
    """Prompt to generate the statistical model (list[BehaviorFormula])."""
    metrics = metrics or BEHAVIOR_METRICS
    user = dedent(
        f"""
        LOCATION: {location_label or "(no name)"}

        REAL LOCATION DATA (anchor everything here):
        {_json(location_stats)}

        TASK:
        Generate ONE BehaviorFormula for each of these metrics:
        {_enum(metrics)}

        For each formula:
        - Set a realistic baseline for this location (use the data: e.g. a
          high median income lowers price_sensitivity; high unemployment raises
          churn_risk).
        - Include at least 3 FactorModifier covering different factors
          (mix age, gender, ethnicity, income, education).
        - Use the real values: if ethnicity_distribution brings "hispanic" and
          "white", the ethnicity segment_value must be those.
        - Write a reproducible expression coherent with combination_rule.

        Return ONLY the JSON array of BehaviorFormula.
        """
    ).strip()
    return {"model": DEFAULT_MODEL, "system": BEHAVIOR_MODEL_SYSTEM, "user": _with_grounding(user, grounding)}


# ===========================================================================
# 2) GROUPS BY FIELD / TOPIC  ->  list[FieldBehaviorGroup]
# ===========================================================================
FIELD_GROUPS_SYSTEM = dedent(
    f"""
    You are an audience strategist. You build synthetic groups with
    behavior CHARACTERISTIC of a field/topic (technology, education,
    entertainment, health, finance, politics, family), focused on how
    they evaluate and adopt a digital product. They are the representatives the
    user uses when they want the reaction of a field-oriented audience.

    Each group is a FieldBehaviorGroup and includes its OWN behavior
    model (behavior_formulas), because each field reacts differently:
    e.g. health weighs privacy/evidence and has low risk tolerance;
    entertainment weighs novelty and has high sharing_propensity.

    {_GUARDRAILS}

    CONTRACTS:
    {_FACTOR_MODIFIER_CONTRACT}

    {_BEHAVIOR_FORMULA_CONTRACT}

    {_FIELD_GROUP_CONTRACT}

    OUTPUT: a JSON array of FieldBehaviorGroup. Nothing else.
    """
).strip()


def build_field_groups_prompt(
    location_stats: dict,
    *,
    location_label: str = "",
    domains: tuple[str, ...] = FIELD_DOMAINS,
    grounding: str = "",
) -> dict:
    """Prompt to generate a FieldBehaviorGroup for each FIELD_DOMAINS domain."""
    user = dedent(
        f"""
        LOCATION: {location_label or "(no name)"}

        REAL LOCATION DATA (to calibrate the groups to the local population):
        {_json(location_stats)}

        TASK:
        Generate ONE FieldBehaviorGroup for each of these fields:
        {_enum(domains)}

        For each group:
        - Ground the profile to the local population (use real income/age for
          typical_income_bracket and typical_age_range).
        - product_evaluation_criteria must reflect the field's lens
          (health: privacy/clinical evidence; finance: ROI/security;
          tech: extensibility/performance; entertainment: novelty; etc.).
        - Include 2-4 behavior_formulas per group, prioritizing
          adoption_propensity, trust_score and engagement_likelihood.

        Return ONLY the JSON array of FieldBehaviorGroup.
        """
    ).strip()
    return {"model": DEFAULT_MODEL, "system": FIELD_GROUPS_SYSTEM, "user": _with_grounding(user, grounding)}


# ===========================================================================
# 3) GROUP PROFILE BY RANGES  ->  GroupBehaviorProfile
# ===========================================================================
GROUP_PROFILE_SYSTEM = dedent(
    f"""
    You are an audience data scientist. You receive the definition of a group
    as a COMBINATION of factors (an age range, a specific ethnicity, a
    gender, an income/social class, a field) and the real data of its location.

    You build a GroupBehaviorProfile: for each behavior metric you give
    a RANGE (min, max, expected), because within the group the levels VARY
    depending on where each person falls on the factors. You also deliver the
    BehaviorFormula that back those ranges, so that the range is the
    result of EVALUATING the formula at the extremes of the group's factor
    spread (not an invented number).

    Important about the ranges (they are the audience's output "scores"):
    - min_value = the formula evaluated at the group's least favorable combination.
    - max_value = the formula evaluated at the most favorable combination.
    - expected_value = the typical value (center of the group).
    - min_driver / max_driver: explain which combination pushes to each extreme.

    {_GUARDRAILS}

    CONTRACTS:
    {_FACTOR_MODIFIER_CONTRACT}

    {_BEHAVIOR_FORMULA_CONTRACT}

    {_GROUP_PROFILE_CONTRACT}

    OUTPUT: a single GroupBehaviorProfile JSON object. Nothing else.
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
    """Prompt to generate a GroupBehaviorProfile (levels by min/max range)."""
    metrics = metrics or BEHAVIOR_METRICS
    user = dedent(
        f"""
        LOCATION: {location_label or "(no name)"}

        GROUP DEFINITION (combination of factors):
        {_json(group_definition)}

        REAL LOCATION DATA (to anchor):
        {_json(location_stats)}

        TASK:
        1. Generate the necessary BehaviorFormula (baseline + modifiers per
           factor) for these metrics: {_enum(metrics)}.
        2. For each metric, compute a MetricRange by evaluating the formula at the
           group's extremes: the min at the least favorable sub-combination and the
           max at the most favorable one, with its expected_value and the drivers.
        3. Assemble a single GroupBehaviorProfile with the group definition,
           the behavior_ranges and the formulas that back them.

        Return ONLY the GroupBehaviorProfile JSON object.
        """
    ).strip()
    return {"model": DEFAULT_MODEL, "system": GROUP_PROFILE_SYSTEM, "user": _with_grounding(user, grounding)}


# ===========================================================================
# 4) REACTION TO A DIGITAL PRODUCT  ->  ReactionProfile
# ===========================================================================
REACTION_SYSTEM = dedent(
    f"""
    You are a synthetic user research panel. You receive (a) a digital
    product asset, (b) an audience segment and (c) the behavior
    model (behavior_formulas) that applies to that segment. You simulate how
    the segment reacts and you CALCULATE the metrics by applying the formulas.

    Do not improvise the numbers: start from the provided formulas, apply the
    modifiers that correspond to the segment and report the result. In
    factor_attribution explain how much each factor pushed (positive or negative).

    {_GUARDRAILS}

    CONTRACT:
    {_REACTION_CONTRACT}

    OUTPUT: a single ReactionProfile JSON object. Nothing else.
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
    """Prompt to generate the ReactionProfile of a segment toward an asset."""
    seccion = f'\nSpecific SECTION to evaluate: "{section}"' if section else ""
    user = dedent(
        f"""
        ASSET (digital product to evaluate):
        {_json(asset)}

        SEGMENT (who you are evaluating):
        {_json(segment)}

        APPLICABLE BEHAVIOR MODEL (use these formulas to calculate):
        {_json(behavior_formulas)}
        {seccion}

        TASK:
        1. For each metric with a formula, apply baseline + the modifiers that
           match the segment's factors, respecting combination_rule and the
           clamp of the expression. Put the result in metric_scores.
        2. Fill sentiment/comprehension/cultural_fit/engagement coherent
           with metric_scores.
        3. In factor_attribution report the net contribution of each factor.
        4. In applied_formula_ids list the formula_id you used.
        5. Give actionable strengths, risks and recommendations to improve the
           product for THIS segment.

        Copy asset_id and segment_id from the input. Return ONLY the
        ReactionProfile JSON object.
        """
    ).strip()
    return {"model": DEFAULT_MODEL, "system": REACTION_SYSTEM, "user": _with_grounding(user, grounding)}


# ===========================================================================
# MOCKS: valid fixtures to run the pipeline without a real model (demo/CI).
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
            "rationale": "Higher income reduces adoption friction (mock).",
            "confidence": 0.6,
        },
        {
            "factor": "age",
            "segment_value": "25-34",
            "effect_type": "multiplier",
            "effect_value": 1.15,
            "weight": 0.3,
            "rationale": "Young adults adopt faster (mock).",
            "confidence": 0.6,
        },
        {
            "factor": "education",
            "segment_value": "bachelor",
            "effect_type": "additive",
            "effect_value": 0.05,
            "weight": 0.3,
            "rationale": "Higher education raises comprehension (mock).",
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
                "description": f"Synthetic group oriented to the {d} field (mock fixture).",
                "typical_age_range": {"min_age": 25, "max_age": 44},
                "typical_income_bracket": "middle",
                "dominant_values": ["quality", "trust"],
                "preferred_platforms": ["instagram", "youtube"],
                "content_format_preferences": ["video", "article"],
                "decision_drivers": ["usefulness", "price"],
                "objections": ["privacy", "learning curve"],
                "jargon_tolerance": 0.5,
                "product_evaluation_criteria": ["usability", "trust"],
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
            "min_driver": "least favorable combination of the group (mock)",
            "max_driver": "most favorable combination of the group (mock)",
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
        "strengths": ["Clear proposition (mock)"],
        "risks": ["Lacks social proof (mock)"],
        "recommendations": ["Add testimonials (mock)"],
        "confidence": 0.6,
        "generated_by": "llm",
    }


# ===========================================================================
# PROMPT REGISTRY (entities)
# ===========================================================================
BEHAVIOR_MODEL_PROMPT = PromptSpec(
    name="behavior_model",
    details=(
        "Builds the statistical behavior model of a location: "
        "a reproducible formula per metric that tells HOW "
        "behavior changes according to gender, age, ethnicity, income/class and education."
    ),
    description_input=(
        "location_stats (dict LocationStatistics: median_income, age_ranges, "
        "ethnicity_distribution, unemployment_rate, poverty_rate, ...), "
        "optional location_label, optional metrics (subset of BEHAVIOR_METRICS), "
        "optional grounding (Foundry IQ evidence)."
    ),
    expected_output="JSON array of BehaviorFormula (>=1 per requested metric).",
    builder=build_behavior_model_prompt,
    output_schema=BehaviorFormulaSchema,
    output_is_list=True,
    mock=mock_behavior_model,
)

FIELD_GROUPS_PROMPT = PromptSpec(
    name="field_groups",
    details=(
        "Generates audience groups oriented to a field/topic (technology, "
        "education, entertainment, health, finance, politics, family), each "
        "with its characteristic behavior and its own model."
    ),
    description_input=(
        "location_stats (dict), optional location_label, optional domains "
        "(subset of FIELD_DOMAINS), optional grounding."
    ),
    expected_output="JSON array of FieldBehaviorGroup (one per requested domain).",
    builder=build_field_groups_prompt,
    output_schema=FieldBehaviorGroupSchema,
    output_is_list=True,
    mock=mock_field_groups,
)

GROUP_PROFILE_PROMPT = PromptSpec(
    name="group_profile",
    details=(
        "Generates the profile of a group defined by a COMBINATION of factors "
        "(age+gender+ethnicity+income+field) with its behavior levels "
        "as RANGES (min/expected/max): the audience output scores."
    ),
    description_input=(
        "group_definition (dict with age_range, gender, ethnicity, "
        "income_bracket, education_level, field_domain), location_stats (dict), "
        "optional location_label, optional metrics, optional grounding."
    ),
    expected_output="GroupBehaviorProfile JSON object with behavior_ranges and formulas.",
    builder=build_group_profile_prompt,
    output_schema=GroupBehaviorProfileSchema,
    output_is_list=False,
    mock=mock_group_profile,
)

REACTION_PROMPT = PromptSpec(
    name="reaction",
    details=(
        "Simulates the reaction of a segment toward a digital product by applying "
        "the behavior model; returns scores and attribution per factor."
    ),
    description_input=(
        "asset (dict ProjectAsset), segment (dict of the segment), "
        "behavior_formulas (list[BehaviorFormula]), optional section, optional grounding."
    ),
    expected_output="ReactionProfile JSON object with 0-1 scores, attribution and feedback.",
    builder=build_reaction_prompt,
    output_schema=ReactionProfileSchema,
    output_is_list=False,
    mock=mock_reaction,
)

# Registry accessible by name.
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
