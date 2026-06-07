from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any

class IngestionEvent(BaseModel):
    session_id: str | None = None
    source: str
    event_type: str
    raw_payload: dict[str, Any]

class AnalyticRecord(BaseModel):
    session_id: str
    audience_id: str | None = None
    recorded_at: datetime = datetime.utcnow()
    engagement_level: float = 0.0
    sentiment_score: float = 0.0
    attention_score: float = 0.0
    conviction_level: float = 0.0
    objection_count: int = 0
    decision_readiness: float = 0.0
    risk_perception: float = 0.0
    pace_wpm: int = 0
    filler_count: int = 0
    clarity_score: float = 0.0
