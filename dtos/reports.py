"""Report DTOs (Pydantic).

Request/result models for end-of-session report generation (PPTX + email
draft), consumed by backend.services.pptx_generator and email_service.

Scaffold stubs — fill in fields as report generation solidifies.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Asks for a report to be generated for a finished session."""

    session_id: UUID
    include_pptx: bool = True
    include_email: bool = True


class ReportResult(BaseModel):
    """The artifacts produced for a session report."""

    session_id: UUID
    pptx_url: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    scores: dict[str, float] = Field(default_factory=dict)
