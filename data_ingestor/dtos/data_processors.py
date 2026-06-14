from marshmallow import Schema, fields, validate

#   Data Processor: here we define the OUTPUT entities. We combine the raw data (Location,
# DemographicGroup) with the synthetic data (SegmentParticularity, Psychographic/Behavioral) so
# that an LLM can extract the general reactions of a segment toward a product/section.

ASSET_TYPES = ("document", "presentation", "spreadsheet", "pdf", "other")


# ---------------------------------------------------------------------------
# Audience: an actionable segment = demographics + particularities + psycho + behavior
# ---------------------------------------------------------------------------
class AudienceSegment(Schema):
    class Meta:
        ordered = True

    segment_id = fields.UUID(required=True)
    label = fields.String(required=True)                 # readable name of the segment

    # References by ID to the ingestor entities (relations, not heavy nesting)
    location_id = fields.UUID(required=True)
    demographic_group_id = fields.UUID(required=True)
    psychographic_group_id = fields.UUID()
    behavioral_group_id = fields.UUID()
    particularity_ids = fields.List(fields.UUID())

    estimated_reach = fields.Integer(validate=validate.Range(min=0))  # reachable people
    confidence = fields.Float(validate=validate.Range(min=0, max=1))  # confidence of the synthetic assembly


# ---------------------------------------------------------------------------
# Asset: the M365 file that OnLooker analyzes
# ---------------------------------------------------------------------------
class ProjectAsset(Schema):
    class Meta:
        ordered = True

    asset_id = fields.UUID(required=True)
    name = fields.String(required=True)
    asset_type = fields.String(required=True, validate=validate.OneOf(ASSET_TYPES))
    summary = fields.String()                            # summary of the content
    language = fields.String()                           # language of the document
    target_segment_ids = fields.List(fields.UUID())      # target audiences (AudienceSegment)
    source_uri = fields.String()                         # location of the file (M365 / Drive)


# ---------------------------------------------------------------------------
# Reaction: what the LLM produces = how a segment reacts to an asset/section
# ---------------------------------------------------------------------------
class ReactionProfile(Schema):
    class Meta:
        ordered = True

    reaction_id = fields.UUID(required=True)
    asset_id = fields.UUID(required=True)                # which asset it reacts to
    segment_id = fields.UUID(required=True)              # which audience reacts
    section = fields.String()                            # specific section/slide/paragraph (optional)

    # Scores normalized 0-1
    sentiment_score = fields.Float(required=True, validate=validate.Range(min=0, max=1))
    comprehension_score = fields.Float(required=True, validate=validate.Range(min=0, max=1))
    cultural_fit_score = fields.Float(required=True, validate=validate.Range(min=0, max=1))
    engagement_likelihood = fields.Float(required=True, validate=validate.Range(min=0, max=1))

    # Actionable qualitative feedback
    strengths = fields.List(fields.String())             # what works well
    risks = fields.List(fields.String())                 # what may fail / offend / confuse
    recommendations = fields.List(fields.String())       # how to improve it for this segment

    confidence = fields.Float(validate=validate.Range(min=0, max=1))
    generated_by = fields.String(load_default="llm")
