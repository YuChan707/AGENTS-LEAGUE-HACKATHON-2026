"""Analytics DTOs (Pydantic).

Models for the streaming/analytics pipeline: the raw events that arrive over
the WebSocket and the analytic records derived from them by the agents. Used
by backend.services.ingestion_service to persist to the DB.

Scaffold stubs — fill in fields as the pipeline solidifies.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class IngestionEvent(BaseModel):
    """A raw event received from the client during a live session
    (transcript chunk, audio metrics, etc.)."""

    session_id: UUID
    seq: int = Field(ge=0)
    kind: str  # e.g. "transcript", "audio", "slide_change"
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[float] = None  # epoch seconds


class AnalyticRecord(BaseModel):
    """A derived analytics datapoint produced by an agent for a given event."""

    session_id: UUID
    source: str  # which agent produced it: speech | audience | coaching | cultural
    metric: str
    value: Any
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
