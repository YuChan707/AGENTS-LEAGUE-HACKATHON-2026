from fastapi import APIRouter
from pydantic import BaseModel

from agents.orchestrator import Orchestrator
from services.ingestion_service import ingestion_service

router = APIRouter(tags=["ingestion_data"])


class IngestionDataRequest(BaseModel):
    session_id: str = "chat"
    text: str
    persona_type: str = "executive"
    region: str = "us"
    focus_area: str = "business"
    environment: str = "professional"
    complexity: str = "medium"
    feedback_setting: str = "academic_us"
    audience_min_age: int = 18
    audience_max_age: int = 45
    audience_amount: int = 100
    source: str = "ingestion_data"
    attach: bool = True


@router.post("/ingestion_data")
async def attach_ingestion_data(req: IngestionDataRequest):
    """Attach ingestion data to the backend AI pipeline and optionally persist events."""
    orch = Orchestrator()
    orch.configure(
        session_id=req.session_id,
        persona=req.persona_type,
        region=req.region,
        focus_area=req.focus_area,
        environment=req.environment,
        complexity=req.complexity,
        feedback_setting=req.feedback_setting,
        audience_min_age=req.audience_min_age,
        audience_max_age=req.audience_max_age,
        audience_amount=req.audience_amount,
    )

    events: list[dict] = []
    async for event in orch.process(req.text):
        event["source"] = req.source
        if req.attach:
            await ingestion_service.ingest(event)
        events.append(event)

    return {
        "session_id": req.session_id,
        "attached": req.attach,
        "event_count": len(events),
        "events": events,
    }
