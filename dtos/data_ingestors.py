import uuid

from marshmallow import Schema, fields, validate, post_load

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

# ---------------------------------------------------------------------------
# Vocabularios para el MODELADO ESTADISTICO del comportamiento ($$ sintetico)
# ---------------------------------------------------------------------------
# Campos/dominios con comportamiento caracteristico (grupos por separado).
FIELD_DOMAINS = (
    "technology", "education", "finance",
    "politics", "entertainment", "family",
)

# Factores demograficos que MODULAN el comportamiento (las "variables" del modelo).
BEHAVIOR_FACTORS = ("age", "gender", "ethnicity", "income", "education", "field")

# Como se aplica el efecto de un factor sobre una metrica base.
#   multiplier -> base * effect_value      (ej: 1.35 = +35%)
#   additive   -> base + effect_value      (ej: +0.12)
#   absolute   -> effect_value             (reemplaza la base para ese valor)
EFFECT_TYPES = ("multiplier", "additive", "absolute")

# Como se combinan varios modificadores sobre la MISMA metrica.
COMBINATION_RULES = ("multiplicative", "additive", "weighted_average")

# Metricas de comportamiento/reaccion que el modelo predice.
# Normalizadas 0-1 salvo que se indique lo contrario en la formula.
BEHAVIOR_METRICS = (
    "adoption_propensity",     # probabilidad de adoptar el producto digital
    "engagement_likelihood",   # probabilidad de interactuar con el
    "retention_probability",   # probabilidad de seguir usandolo
    "churn_risk",              # riesgo de abandono
    "sentiment_score",         # sentimiento hacia el producto
    "comprehension_score",     # que tan bien entiende la propuesta
    "trust_score",             # confianza en el producto / marca
    "price_sensitivity",       # sensibilidad al precio (1 = muy sensible)
    "sharing_propensity",      # propension a recomendar / compartir
    "conversion_rate",         # probabilidad de conversion
)


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
    age_ranges = fields.Dict(keys=fields.String(), values=fields.Float(validate=validate.Range(min=0, max=100)))  # %  de edades
    ethnicity_distribution = fields.Dict(keys=fields.String(), values=fields.Float(validate=validate.Range(min=0, max=100)))  # % por etnia


class LocationEntity:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Demographics Info  (identidad de la ubicacion)
class Location(Schema):
    class Meta:
        ordered = True

    location_id = fields.UUID(required=True)
    coordinates = fields.Nested(GeoPoint, required=True, allow_none=True)  # Centroide del sitio
    zip_code = fields.String(required=True, allow_none=True)
    country = fields.String(required=True)
    state = fields.String(required=True)
    city = fields.String(required=True)
    total_population = fields.Integer(required=True)
    last_updated = fields.Date()

    # Metadata estadistica (nested, no aplanada)
    statistics = fields.Nested(LocationStatistics, required=False)

    # Procedencia de la data cruda

    @post_load
    def make_location(self, data, **kwargs):
        return LocationEntity(**data)

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

    preferred_platforms = fields.List(fields.String())
    content_format_preferences = fields.List(fields.String())
    peak_activity_hours = fields.List(fields.Integer(validate=validate.Range(min=0, max=23)))
    avg_session_minutes = fields.Float(validate=validate.Range(min=0))
    engagement_style = fields.String()                      # ej: "lurker", "creator", "sharer"
    price_sensitivity = fields.Float(validate=validate.Range(min=0, max=1))
    sharing_propensity = fields.Float(validate=validate.Range(min=0, max=1))

    generated_by = fields.String(load_default="llm")


# ===========================================================================
# MODELO ESTADISTICO DEL COMPORTAMIENTO  ($$ Data Sintetica)
#   Permite a la LLM expresar COMO cambia una metrica de comportamiento segun
#   factores demograficos (edad, genero, etnia, income...) mediante formulas
#   reproducibles, no solo valores planos. Enfocado a evaluar un producto digital.
# ===========================================================================

# Efecto cuantificado de UN valor de UN factor sobre una metrica base.
# Ej: factor="income", segment_value="low", effect_type="multiplier", effect_value=1.4
#     -> "los de ingreso bajo tienen 40% mas de price_sensitivity".
class FactorModifier(Schema):
    class Meta:
        ordered = True

    factor = fields.String(required=True, validate=validate.OneOf(BEHAVIOR_FACTORS))
    segment_value = fields.String(required=True)   # "18-24", "female", "hispanic", "low", "technology"...
    effect_type = fields.String(required=True, validate=validate.OneOf(EFFECT_TYPES))
    effect_value = fields.Float(required=True)      # 1.35 (mult), +0.12 (add), 0.7 (abs)
    weight = fields.Float(validate=validate.Range(min=0, max=1))  # peso si combination_rule = weighted_average
    rationale = fields.String(required=True)        # justificacion de la LLM (por que ese efecto)
    confidence = fields.Float(validate=validate.Range(min=0, max=1))


# Formula estadistica que predice UNA metrica: base + modificadores por factor.
# La expresion es reproducible: dado un segmento concreto se puede calcular el valor.
class BehaviorFormula(Schema):
    class Meta:
        ordered = True

    formula_id = fields.UUID(required=True)
    metric = fields.String(required=True, validate=validate.OneOf(BEHAVIOR_METRICS))
    baseline = fields.Float(required=True)          # valor base (poblacion de referencia) antes de modificar
    combination_rule = fields.String(required=True, validate=validate.OneOf(COMBINATION_RULES))
    modifiers = fields.List(fields.Nested(FactorModifier), required=True)
    expression = fields.String(required=True)       # legible: "adoption = base * Π(mult) + Σ(add), clamp[0,1]"
    output_min = fields.Float(load_default=0.0)
    output_max = fields.Float(load_default=1.0)
    sample_size = fields.Integer(validate=validate.Range(min=0))  # n sintetico que respalda la estimacion
    confidence = fields.Float(validate=validate.Range(min=0, max=1))
    generated_by = fields.String(load_default="llm")


# Grupo con comportamiento caracteristico de un CAMPO (tech, educacion, finanzas,
# politica, entretenimiento, familia), con su propio modelo de comportamiento y
# su lente para evaluar un producto digital.
class FieldBehaviorGroup(Schema):
    class Meta:
        ordered = True

    group_id = fields.UUID(required=True)
    group_name = fields.String(required=True)
    field_domain = fields.String(required=True, validate=validate.OneOf(FIELD_DOMAINS))
    description = fields.String(required=True)

    # Perfil tipico (referencia demografica suave, no nesteo duro)
    typical_age_range = fields.Nested(AgeRange)
    typical_income_bracket = fields.String(validate=validate.OneOf(INCOME_BRACKETS))
    dominant_values = fields.List(fields.String())

    # Conducta online caracteristica
    preferred_platforms = fields.List(fields.String())
    content_format_preferences = fields.List(fields.String())
    decision_drivers = fields.List(fields.String())        # que pesa al decidir adoptar
    objections = fields.List(fields.String())              # frenos / razones de rechazo tipicas
    jargon_tolerance = fields.Float(validate=validate.Range(min=0, max=1))

    # Lente con la que evaluan un producto digital
    product_evaluation_criteria = fields.List(fields.String())  # ["privacidad", "ROI", "usabilidad"...]

    # Modelo estadistico de comportamiento propio de este grupo
    behavior_formulas = fields.List(fields.Nested(BehaviorFormula))

    generated_by = fields.String(load_default="llm")


# Rango [min, max] que puede tomar UNA metrica para un grupo. Las formulas no
# devuelven un solo numero: al evaluarse sobre el ABANICO de valores de los
# factores del grupo (varios buckets de edad, etc.) producen un minimo y un
# maximo. expected_value es el valor central/esperado.
class MetricRange(Schema):
    class Meta:
        ordered = True

    metric = fields.String(required=True, validate=validate.OneOf(BEHAVIOR_METRICS))
    min_value = fields.Float(required=True)
    max_value = fields.Float(required=True)
    expected_value = fields.Float()        # tipico/medio dentro del rango
    min_driver = fields.String()           # combinacion de factores que lleva al minimo
    max_driver = fields.String()           # combinacion de factores que lleva al maximo
    formula_id = fields.UUID()             # de que BehaviorFormula sale este rango


# Especificacion GUARDADA de la LLM: un grupo definido por la COMBINACION de
# factores (rango de edad + etnia + genero + income + campo) y como varian sus
# niveles de comportamiento ENTRE un minimo y un maximo. Es la entidad que el
# data_processor persiste para luego calcular reacciones.
#   Ej: edad 25-44, etnia "asian", genero "male", campo "technology"
#       -> adoption_propensity entre 0.52 y 0.78, etc.
class GroupBehaviorProfile(Schema):
    class Meta:
        ordered = True

    profile_id = fields.UUID(required=True)
    group_name = fields.String(required=True)
    location_id = fields.UUID()            # opcional: a que Location aplica

    # --- Definicion del grupo por COMBINACION de factores ---
    age_range = fields.Nested(AgeRange)                                  # rango de edad
    gender = fields.String(validate=validate.OneOf(GENDERS))
    ethnicity = fields.String()
    income_bracket = fields.String(validate=validate.OneOf(INCOME_BRACKETS))
    education_level = fields.String(validate=validate.OneOf(EDUCATION_LEVELS))
    field_domain = fields.String(validate=validate.OneOf(FIELD_DOMAINS))

    # --- Niveles de comportamiento como RANGOS (min/max/esperado) ---
    behavior_ranges = fields.List(fields.Nested(MetricRange), required=True)

    # --- Formulas que generan esos rangos (trazabilidad + recalculo) ---
    formulas = fields.List(fields.Nested(BehaviorFormula))

    confidence = fields.Float(validate=validate.Range(min=0, max=1))
    generated_by = fields.String(load_default="llm")
