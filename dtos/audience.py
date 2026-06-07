"""Audience DTOs (Pydantic).

Shared models describing target audiences. Mirrors, in Pydantic form, the
synthetic-segment concepts defined with Marshmallow in data_processors.py
(AudienceSegment) and data_ingestors.py (demographic/psychographic/behavioral
groups).

Scaffold stubs — fill in fields as the API/agents need them.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AudienceProfile(BaseModel):
    """A single actionable audience segment: demographics + psychographics +
    behavior, used to condition the audience persona agent."""

    segment_id: UUID
    label: str

    # Free-form descriptors for the persona (kept loose for the scaffold).
    region: Optional[str] = None
    values: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    preferred_platforms: list[str] = Field(default_factory=list)

    estimated_reach: Optional[int] = Field(default=None, ge=0)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class AudienceGroup(BaseModel):
    """A named collection of audience profiles (e.g. the audience selected for
    a session)."""

    group_id: UUID
    group_name: str
    profiles: list[AudienceProfile] = Field(default_factory=list)
