from marshmallow import Schema, fields, validate

#   Data Processor: aqui definimos las entidades de SALIDA. Combinamos la data cruda (Location,
# DemographicGroup) con la data sintetica (SegmentParticularity, Psychographic/Behavioral) para
# que una LLM pueda extraer las reacciones generales de un segmento frente a un producto/seccion.

ASSET_TYPES = ("document", "presentation", "spreadsheet", "pdf", "other")


# ---------------------------------------------------------------------------
# Audiencia: un segmento accionable = demografia + particularidades + psico + conducta
# ---------------------------------------------------------------------------
class AudienceSegment(Schema):
    class Meta:
        ordered = True

    segment_id = fields.UUID(required=True)
    label = fields.String(required=True)                 # nombre legible del segmento

    # Referencias por ID a las entidades del ingestor (relaciones, no nesteo pesado)
    location_id = fields.UUID(required=True)
    demographic_group_id = fields.UUID(required=True)
    psychographic_group_id = fields.UUID()
    behavioral_group_id = fields.UUID()
    particularity_ids = fields.List(fields.UUID())

    estimated_reach = fields.Integer(validate=validate.Range(min=0))  # personas alcanzables
    confidence = fields.Float(validate=validate.Range(min=0, max=1))  # confianza del armado sintetico


# ---------------------------------------------------------------------------
# Asset: el archivo M365 que OnLooker analiza
# ---------------------------------------------------------------------------
class ProjectAsset(Schema):
    class Meta:
        ordered = True

    asset_id = fields.UUID(required=True)
    name = fields.String(required=True)
    asset_type = fields.String(required=True, validate=validate.OneOf(ASSET_TYPES))
    summary = fields.String()                            # resumen del contenido
    language = fields.String()                           # idioma del documento
    target_segment_ids = fields.List(fields.UUID())      # audiencias objetivo (AudienceSegment)
    source_uri = fields.String()                         # ubicacion del archivo (M365 / Drive)


# ---------------------------------------------------------------------------
# Reaccion: lo que produce la LLM = como reacciona un segmento a un asset/seccion
# ---------------------------------------------------------------------------
class ReactionProfile(Schema):
    class Meta:
        ordered = True

    reaction_id = fields.UUID(required=True)
    asset_id = fields.UUID(required=True)                # a que asset reacciona
    segment_id = fields.UUID(required=True)              # que audiencia reacciona
    section = fields.String()                            # seccion/slide/parrafo especifico (opcional)

    # Scores normalizados 0-1
    sentiment_score = fields.Float(required=True, validate=validate.Range(min=0, max=1))
    comprehension_score = fields.Float(required=True, validate=validate.Range(min=0, max=1))
    cultural_fit_score = fields.Float(required=True, validate=validate.Range(min=0, max=1))
    engagement_likelihood = fields.Float(required=True, validate=validate.Range(min=0, max=1))

    # Feedback cualitativo accionable
    strengths = fields.List(fields.String())             # que funciona bien
    risks = fields.List(fields.String())                 # que puede fallar / ofender / confundir
    recommendations = fields.List(fields.String())       # como mejorarlo para este segmento

    confidence = fields.Float(validate=validate.Range(min=0, max=1))
    generated_by = fields.String(load_default="llm")
