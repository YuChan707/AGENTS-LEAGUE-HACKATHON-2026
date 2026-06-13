from marshmallow import Schema, fields, validate

#     Data Ingestor es donde se va a extraer la data que se necesita y se va a almacenar en las
# entidades necesarias para luego integrarlas al data processor.
#   - Data CRUDA  : se extrae de Data Commons (estadistica real por ubicacion, foco en NY, USA).
#   - Data SINTETICA ($$): se genera con ayuda de LLMs a partir de la data cruda.

# ---------------------------------------------------------------------------
# Vocabularios controlados (enums) para evitar precariedad / valores libres
# ---------------------------------------------------------------------------
GENDERS = ("male", "female", "non_binary", "other")
EDUCATION_LEVELS = (
    "none", "primary", "secondary", "high_school",
    "associate", "bachelor", "master", "doctorate",
)
INCOME_BRACKETS = ("low", "lower_middle", "middle", "upper_middle", "high")
PARTICULARITY_DIMENSIONS = ("gender", "ethnicity", "income", "field")


def percentage():
    """Float 0-100 reutilizable para tasas (unemployment, poverty, etc.)."""
    return fields.Float(required=True, validate=validate.Range(min=0, max=100))


# ===========================================================================
# DATA CRUDA  (Data Commons)
# ===========================================================================
# Rango etario reutilizable (un rango NO es un solo numero)
class AgeRange(Schema):
    min_age = fields.Integer(required=True, validate=validate.Range(min=0, max=120))
    max_age = fields.Integer(required=True, validate=validate.Range(min=0, max=120))


# Punto geografico simple (centroide del lugar)
class GeoPoint(Schema):
    latitude = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180, max=180))


# Metadata estadistica de una ubicacion: la separamos de la identidad para que
# cada bloque tenga responsabilidad unica y sea facil de nestear/versionar.
class LocationStatistics(Schema):
    unemployment_rate = percentage()      # % de desempleo
    poverty_rate = percentage()           # % bajo linea de pobreza
    cost_of_living_index = fields.Float(required=True)   # indice (100 = media nacional)
    median_income = fields.Integer(required=True)        # ingreso mediano anual (USD)
    avg_household_size = fields.Float(required=True)      # tamano medio del hogar
    safety_index = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    avg_education= fields.Float(required=True)
    avg_female_population = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    avg_male_population = fields.Float(required=True, validate=validate.Range(min=0, max=100))  
    total_population = fields.Integer(required=True)         # poblacion total
    age_ranges = fields.Dict(keys=fields.Nested(AgeRange), values=fields.Float(validate=validate.Range(min=0, max=100)))  # %  de edades
    ethnicity_distribution = fields.Dict(keys=fields.String(), values=fields.Float(validate=validate.Range(min=0, max=100)))  # % por etnia



# Demographics Info  (identidad de la ubicacion)
class Location(Schema):
    class Meta:
        ordered = True

    # Identidad
    location_id = fields.UUID(required=True)             # ID interno para relacionar (busqueda barata)
    dcid = fields.String(required=True)                  # Data Commons ID (ej: "geoId/36")
    location_name = fields.String(required=True)         # Nombre claro
    coordinates = fields.Nested(GeoPoint, required=True)  # Centroide del sitio
    zip_code = fields.String(required=True)
    country = fields.String(required=True)
    state = fields.String(required=True)
    city = fields.String(required=True)

    # Metadata estadistica (nested, no aplanada)
    statistics = fields.Nested(LocationStatistics, required=True)

    # Procedencia de la data cruda
    data_source = fields.String(load_default="datacommons.org")
    last_updated = fields.Date()


# Grupo demografico extraido de la data cruda
class DemographicGroup(Schema):
    class Meta:
        ordered = True

    group_id = fields.UUID(required=True)
    group_name = fields.String(required=True)
    location_id = fields.UUID(required=True)             # referencia a Location (no nested completo)

    # Atributos demograficos
    age_range = fields.Nested(AgeRange, required=True)
    gender = fields.String(validate=validate.OneOf(GENDERS))
    ethnicity = fields.String()
    education_level = fields.String(validate=validate.OneOf(EDUCATION_LEVELS))
    income_bracket = fields.String(validate=validate.OneOf(INCOME_BRACKETS))
    median_income = fields.Integer()

    # Tamano del grupo
    population_size = fields.Integer(required=True, validate=validate.Range(min=0))
    population_share = fields.Float(validate=validate.Range(min=0, max=1))  # proporcion dentro de la location


# ===========================================================================
# FILTROS ESPECIFICOS  ($$ Data Sintetica)
# ===========================================================================

# Particularidad de un segmento, parametrica por "dimension".
# Reemplaza las antiguas Gender/Ethnicity/Income/FieldParticularities en una sola entidad.
class SegmentParticularity(Schema):
    class Meta:
        ordered = True

    particularity_id = fields.UUID(required=True)
    dimension = fields.String(required=True, validate=validate.OneOf(PARTICULARITY_DIMENSIONS))
    label = fields.String(required=True)                 # ej: "female", "latino", "middle", "tech"
    description = fields.String(required=True)           # explicacion generada por la LLM

    # Atributos libres segun la dimension (ej: cultural_values, price_sensitivity, jargon_tolerance...)
    attributes = fields.Dict(keys=fields.String(), values=fields.Raw())
    traits = fields.List(fields.String())                # rasgos clave en lenguaje natural

    generated_by = fields.String(load_default="llm")     # trazabilidad de data sintetica


# ===========================================================================
# CONSUMIDORES ONLINE  ($$ Data Sintetica)
# ===========================================================================

# Grupo psicografico: valores, intereses, estilo de vida, actitudes.
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


# Grupo conductual: como se comportan online (basado en el conocimiento general de la LLM).
class BehavioralGroup(Schema):
    class Meta:
        ordered = True

    group_id = fields.UUID(required=True)
    group_name = fields.String(required=True)

    preferred_platforms = fields.List(fields.String())      # ej: ["instagram", "linkedin"]
    content_format_preferences = fields.List(fields.String())  # ej: ["video", "carrusel"]
    peak_activity_hours = fields.List(fields.Integer(validate=validate.Range(min=0, max=23)))
    avg_session_minutes = fields.Float(validate=validate.Range(min=0))
    engagement_style = fields.String()                      # ej: "lurker", "creator", "sharer"
    price_sensitivity = fields.Float(validate=validate.Range(min=0, max=1))
    sharing_propensity = fields.Float(validate=validate.Range(min=0, max=1))

    generated_by = fields.String(load_default="llm")
