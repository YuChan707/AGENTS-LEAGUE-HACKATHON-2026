from marshmallow import Schema, fields

from datetime import date
from pprint import pprint

# El Esquema de los datos de los grupos de audiencias identificados distribucion de grupos por zona geografica y otros ...
class GroupAudienceSchema(Schema):
    group_audience_id = fields.UUID(required=True)
    name_audience = fields.String(required=True)
    audience_metadata = fields.Nested(AudienceSchema, required=True, many=True)



class AudienceSchema(Schema):