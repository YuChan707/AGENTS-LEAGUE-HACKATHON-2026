from pydantic import BaseModel
from uuid import UUID
from typing import Any

class AudienceProfile(BaseModel):
    persona_type: str
    region: str
    focus_area: str
    demographic_data: dict[str, Any] = {}
    behavioral_profile: dict[str, Any] = {}
    group_label: str = ""
    group_size_estimate: int = 0

class AudienceGroup(BaseModel):
    session_id: str
    group_label: str
    focus_area: str
    behavioral_pattern: str
    recommended_approach: str
    confidence_score: float = 0.0
    member_count: int = 0
