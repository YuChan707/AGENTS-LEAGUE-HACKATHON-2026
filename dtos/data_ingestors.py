
from marshmallow import Schema, fields, validate, post_load

#     Data Ingestor is where the needed data is extracted and stored in the
# entities required to later integrate them into the data processor.
#   - RAW Data  : extracted from Data Commons (real statistics per location, focus on NY, USA).
#   - SYNTHETIC Data ($$): generated with the help of LLMs from the raw data.

# ---------------------------------------------------------------------------
# Controlled vocabularies (enums) to avoid precariousness / free-form values
# ---------------------------------------------------------------------------
GENDERS = ("male", "female", "non_binary", "other")
EDUCATION_LEVELS = (
    "none", "primary", "secondary", "high_school",
    "associate", "bachelor", "master", "doctorate",
)
INCOME_BRACKETS = ("low", "lower_middle", "middle", "upper_middle", "high")
PARTICULARITY_DIMENSIONS = ("gender", "ethnicity", "income", "field")

# ---------------------------------------------------------------------------
# Vocabularies for the STATISTICAL MODELING of behavior ($$ synthetic)
# ---------------------------------------------------------------------------
# Fields/domains with characteristic behavior (separate groups).
# Technology, Education, Entertainment and Health are the main
# representatives when the user wants the reaction of an audience of a field.
FIELD_DOMAINS = (
    "technology", "education", "finance",
    "politics", "entertainment", "family", "health",
)

# Demographic factors that MODULATE behavior (the "variables" of the model).
BEHAVIOR_FACTORS = ("age", "gender", "ethnicity", "income", "education", "field")

# How the effect of a factor is applied over a base metric.
#   multiplier -> base * effect_value      (e.g.: 1.35 = +35%)
#   additive   -> base + effect_value      (e.g.: +0.12)
#   absolute   -> effect_value             (replaces the base for that value)
EFFECT_TYPES = ("multiplier", "additive", "absolute")

# How several modifiers over the SAME metric are combined.
COMBINATION_RULES = ("multiplicative", "additive", "weighted_average")

# Behavior/reaction metrics that the model predicts.
# Normalized 0-1 unless otherwise indicated in the formula.
BEHAVIOR_METRICS = (
    "adoption_propensity",     # probability of adopting the digital product
    "engagement_likelihood",   # probability of interacting with it
    "retention_probability",   # probability of continuing to use it
    "churn_risk",              # abandonment risk
    "sentiment_score",         # sentiment toward the product
    "comprehension_score",     # how well the proposal is understood
    "trust_score",             # trust in the product / brand
    "price_sensitivity",       # price sensitivity (1 = very sensitive)
    "sharing_propensity",      # propensity to recommend / share
    "conversion_rate",         # conversion probability
)


def percentage():
    """Reusable Float 0-100 for rates (unemployment, poverty, etc.)."""
    return fields.Float(required=True, validate=validate.Range(min=0, max=100))


# ===========================================================================
# RAW DATA  (Data Commons)
# ===========================================================================
# Reusable age range (a range is NOT a single number)
class AgeRange(Schema):
    min_age = fields.Integer(required=True, validate=validate.Range(min=0, max=120))
    max_age = fields.Integer(required=True, validate=validate.Range(min=0, max=120))


# Simple geographic point (centroid of the place)
class GeoPoint(Schema):
    latitude = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180, max=180))


# Statistical metadata of a location: we separate it from the identity so that
# each block has a single responsibility and is easy to nest/version.
class LocationStatistics(Schema):
    unemployment_rate = percentage()      # % unemployment
    poverty_rate = percentage()           # % below poverty line
    cost_of_living_index = fields.Float(required=True)   # index (100 = national average)
    median_income = fields.Integer(required=True)        # annual median income (USD)
    avg_household_size = fields.Float(required=True)      # average household size
    safety_index = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    avg_education= fields.Float(required=True)
    avg_female_population = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    avg_male_population = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    age_ranges = fields.Dict(keys=fields.String(), values=fields.Float(validate=validate.Range(min=0, max=100)))  # %  of ages
    ethnicity_distribution = fields.Dict(keys=fields.String(), values=fields.Float(validate=validate.Range(min=0, max=100)))  # % by ethnicity


class LocationEntity:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Demographics Info  (location identity)
class Location(Schema):
    class Meta:
        ordered = True

    location_id = fields.UUID(required=True)
    coordinates = fields.Nested(GeoPoint, required=True, allow_none=True)  # Centroid of the site
    zip_code = fields.String(required=True, allow_none=True)
    country = fields.String(required=True)
    state = fields.String(required=True)
    city = fields.String(required=True)
    total_population = fields.Integer(required=True)
    last_updated = fields.Date()

    # Statistical metadata (nested, not flattened)
    statistics = fields.Nested(LocationStatistics, required=False)

    # Provenance of the raw data

    @post_load
    def make_location(self, data, **kwargs):
        return LocationEntity(**data)

# Demographic group extracted from the raw data
class DemographicGroup(Schema):
    class Meta:
        ordered = True

    group_id = fields.UUID(required=True)
    group_name = fields.String(required=True)
    location_id = fields.UUID(required=True)             # reference to Location (not full nested)

    # Demographic attributes
    age_range = fields.Nested(AgeRange, required=True)
    gender = fields.String(validate=validate.OneOf(GENDERS))
    ethnicity = fields.String()
    education_level = fields.String(validate=validate.OneOf(EDUCATION_LEVELS))
    income_bracket = fields.String(validate=validate.OneOf(INCOME_BRACKETS))
    median_income = fields.Integer()

    # Group size
    population_size = fields.Integer(required=True, validate=validate.Range(min=0))
    population_share = fields.Float(validate=validate.Range(min=0, max=1))  # proportion within the location


# ===========================================================================
# SPECIFIC FILTERS  ($$ Synthetic Data)
# ===========================================================================

# Particularity of a segment, parametric by "dimension".
# Replaces the old Gender/Ethnicity/Income/FieldParticularities into a single entity.
class SegmentParticularity(Schema):
    class Meta:
        ordered = True

    particularity_id = fields.UUID(required=True)
    dimension = fields.String(required=True, validate=validate.OneOf(PARTICULARITY_DIMENSIONS))
    label = fields.String(required=True)                 # e.g.: "female", "latino", "middle", "tech"
    description = fields.String(required=True)           # explanation generated by the LLM

    # Free attributes depending on the dimension (e.g.: cultural_values, price_sensitivity, jargon_tolerance...)
    attributes = fields.Dict(keys=fields.String(), values=fields.Raw())
    traits = fields.List(fields.String())                # key traits in natural language

    generated_by = fields.String(load_default="llm")     # traceability of synthetic data


# ===========================================================================
# ONLINE CONSUMERS  ($$ Synthetic Data)
# ===========================================================================

# Psychographic group: values, interests, lifestyle, attitudes.
class PsychographicGroup(Schema):
    class Meta:
        ordered = True

    group_id = fields.UUID(required=True)
    group_name = fields.String(required=True)

    values = fields.List(fields.String())
    interests = fields.List(fields.String())
    lifestyle = fields.List(fields.String())
    personality_traits = fields.List(fields.String())
    motivations = fields.List(fields.String())
    attitudes = fields.List(fields.String())

    generated_by = fields.String(load_default="llm")


# Behavioral group: how they behave online (based on the LLM's general knowledge).
class BehavioralGroup(Schema):
    class Meta:
        ordered = True

    group_id = fields.UUID(required=True)
    group_name = fields.String(required=True)

    preferred_platforms = fields.List(fields.String())
    content_format_preferences = fields.List(fields.String())
    peak_activity_hours = fields.List(fields.Integer(validate=validate.Range(min=0, max=23)))
    avg_session_minutes = fields.Float(validate=validate.Range(min=0))
    engagement_style = fields.String()                      # e.g.: "lurker", "creator", "sharer"
    price_sensitivity = fields.Float(validate=validate.Range(min=0, max=1))
    sharing_propensity = fields.Float(validate=validate.Range(min=0, max=1))

    generated_by = fields.String(load_default="llm")


# ===========================================================================
# STATISTICAL MODEL OF BEHAVIOR  ($$ Synthetic Data)
#   Lets the LLM express HOW a behavior metric changes according to
#   demographic factors (age, gender, ethnicity, income...) through
#   reproducible formulas, not just flat values. Focused on evaluating a digital product.
# ===========================================================================

# Quantified effect of ONE value of ONE factor over a base metric.
# E.g.: factor="income", segment_value="low", effect_type="multiplier", effect_value=1.4
#     -> "low-income people have 40% more price_sensitivity".
class FactorModifier(Schema):
    class Meta:
        ordered = True

    factor = fields.String(required=True, validate=validate.OneOf(BEHAVIOR_FACTORS))
    segment_value = fields.String(required=True)   # "18-24", "female", "hispanic", "low", "technology"...
    effect_type = fields.String(required=True, validate=validate.OneOf(EFFECT_TYPES))
    effect_value = fields.Float(required=True)      # 1.35 (mult), +0.12 (add), 0.7 (abs)
    weight = fields.Float(validate=validate.Range(min=0, max=1))  # weight if combination_rule = weighted_average
    rationale = fields.String(required=True)        # LLM's justification (why that effect)
    confidence = fields.Float(validate=validate.Range(min=0, max=1))


# Statistical formula that predicts ONE metric: base + modifiers per factor.
# The expression is reproducible: given a concrete segment the value can be computed.
class BehaviorFormula(Schema):
    class Meta:
        ordered = True

    formula_id = fields.UUID(required=True)
    metric = fields.String(required=True, validate=validate.OneOf(BEHAVIOR_METRICS))
    baseline = fields.Float(required=True)          # base value (reference population) before modifying
    combination_rule = fields.String(required=True, validate=validate.OneOf(COMBINATION_RULES))
    modifiers = fields.List(fields.Nested(FactorModifier), required=True)
    expression = fields.String(required=True)       # readable: "adoption = base * Π(mult) + Σ(add), clamp[0,1]"
    output_min = fields.Float(load_default=0.0)
    output_max = fields.Float(load_default=1.0)
    sample_size = fields.Integer(validate=validate.Range(min=0))  # synthetic n backing the estimate
    confidence = fields.Float(validate=validate.Range(min=0, max=1))
    generated_by = fields.String(load_default="llm")


# Group with characteristic behavior of a FIELD (tech, education, finance,
# politics, entertainment, family), with its own behavior model and
# its lens for evaluating a digital product.
class FieldBehaviorGroup(Schema):
    class Meta:
        ordered = True

    group_id = fields.UUID(required=True)
    group_name = fields.String(required=True)
    field_domain = fields.String(required=True, validate=validate.OneOf(FIELD_DOMAINS))
    description = fields.String(required=True)

    # Typical profile (soft demographic reference, not hard nesting)
    typical_age_range = fields.Nested(AgeRange)
    typical_income_bracket = fields.String(validate=validate.OneOf(INCOME_BRACKETS))
    dominant_values = fields.List(fields.String())

    # Characteristic online behavior
    preferred_platforms = fields.List(fields.String())
    content_format_preferences = fields.List(fields.String())
    decision_drivers = fields.List(fields.String())        # what weighs when deciding to adopt
    objections = fields.List(fields.String())              # blockers / typical rejection reasons
    jargon_tolerance = fields.Float(validate=validate.Range(min=0, max=1))

    # Lens through which they evaluate a digital product
    product_evaluation_criteria = fields.List(fields.String())  # ["privacy", "ROI", "usability"...]

    # Statistical behavior model specific to this group
    behavior_formulas = fields.List(fields.Nested(BehaviorFormula))

    generated_by = fields.String(load_default="llm")


# Range [min, max] that ONE metric can take for a group. Formulas do not
# return a single number: when evaluated over the SPREAD of values of the
# group's factors (several age buckets, etc.) they produce a minimum and a
# maximum. expected_value is the central/expected value.
class MetricRange(Schema):
    class Meta:
        ordered = True

    metric = fields.String(required=True, validate=validate.OneOf(BEHAVIOR_METRICS))
    min_value = fields.Float(required=True)
    max_value = fields.Float(required=True)
    expected_value = fields.Float()        # typical/average within the range
    min_driver = fields.String()           # combination of factors leading to the minimum
    max_driver = fields.String()           # combination of factors leading to the maximum
    formula_id = fields.UUID()             # which BehaviorFormula this range comes from


# SAVED specification from the LLM: a group defined by the COMBINATION of
# factors (age range + ethnicity + gender + income + field) and how its
# behavior levels vary BETWEEN a minimum and a maximum. It is the entity that
# the data_processor persists to later compute reactions.
#   E.g.: age 25-44, ethnicity "asian", gender "male", field "technology"
#       -> adoption_propensity between 0.52 and 0.78, etc.
class GroupBehaviorProfile(Schema):
    class Meta:
        ordered = True

    profile_id = fields.UUID(required=True)
    group_name = fields.String(required=True)
    location_id = fields.UUID()            # optional: which Location it applies to

    # --- Definition of the group by COMBINATION of factors ---
    age_range = fields.Nested(AgeRange)                                  # age range
    gender = fields.String(validate=validate.OneOf(GENDERS))
    ethnicity = fields.String()
    income_bracket = fields.String(validate=validate.OneOf(INCOME_BRACKETS))
    education_level = fields.String(validate=validate.OneOf(EDUCATION_LEVELS))
    field_domain = fields.String(validate=validate.OneOf(FIELD_DOMAINS))

    # --- Behavior levels as RANGES (min/max/expected) ---
    behavior_ranges = fields.List(fields.Nested(MetricRange), required=True)

    # --- Formulas that generate those ranges (traceability + recompute) ---
    formulas = fields.List(fields.Nested(BehaviorFormula))

    confidence = fields.Float(validate=validate.Range(min=0, max=1))
    generated_by = fields.String(load_default="llm")
