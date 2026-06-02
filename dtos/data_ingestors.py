from marshmallow import Schema, fields

from datetime import date
from pprint import pprint

# things to have in count: 1LVL location, 2LVL Income, 4LVL Gender, 3LVL Age
class Locations(Schema):
    class Meta(Schema.Meta):
        fields = (
            "location_id",
            "location_name",
            "location_coordinates",
            "location_country",
            "location_city",
            "location_state",
            "location_zip_code",
            "location_meta",
        )

    # Location Idy
    location_id = fields.UUID(required=True)
    location_name = fields.String(required=True)
    location_coordinates = fields.List(fields.List(fields.Float), required=True)
    location_zip_code = fields.String(required=True)
    location_country = fields.String(required=True)
    location_state = fields.String(required=True)
    location_city = fields.String(required=True)

    # Metadata Location
    unemployment_rate = fields.Integer(required=True)
    life_cost = fields.Integer(required=True)
    poverty_rate = fields.Integer(required=True)
    average_income = fields.Integer(required=True)
    avg_familiar_groups = fields.Integer(required=True)
    security_rate = fields.Integer(required=True)

    location_meta = fields.Nested(
        "self",
        only=("unemployment_rate", "life_cost", "poverty_rate", "average_income", "avg_familiar_groups",
              "security_rate")
    )
    group_relations = fields.Nested("group_ids", many=True)

class DemographicsGroups(Schema):
    class Meta(Schema.Meta):
        fields = (
            "group_id",
            "group_name",
            "group_type",
            "group_location",
            "age_range",
            "education_level",
            "avg_income",
            "gender_level",
        )

    group_id = fields.UUID(required=True)
    group_name = fields.String(required=True)
    group_type = fields.String(required=True)
    group_location =fields.Nested(Locations)

    age_range =fields.Float(required=True)
    education_level = fields.Integer(required=True)
    avg_income = fields.Float(required=True)
    gender_level = fields.Integer(required=True)



# Specifiquitions edit for gender and location

