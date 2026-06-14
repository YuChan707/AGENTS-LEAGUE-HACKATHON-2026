from pydantic import BaseModel
from typing import Any

class ReportRequest(BaseModel):
    session_id: str
    report_types: list[str]
    persona_type: str
    region: str
    focus_area: str

class ReportResult(BaseModel):
    session_id: str
    pptx_url: str | None = None
    email_draft: dict | None = None
    qa_transcript: list[dict] | None = None
    summary: dict[str, Any] | None = None
