
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
