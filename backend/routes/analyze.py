from fastapi import APIRouter
from pydantic import BaseModel
from agents.orchestrator import Orchestrator

router = APIRouter(tags=["analyze"])


class ChunkRequest(BaseModel):
    text: str
    session_id: str = "chat"
    persona_type: str = "executive"
    region: str = "us"
    focus_area: str = "business"
    environment: str = "professional"
    complexity: str = "medium"
    feedback_setting: str = "academic_us"
    audience_min_age: int = 18
    audience_max_age: int = 45
    audience_amount: int = 100


@router.post("/analyze/chunk")
async def analyze_chunk(req: ChunkRequest):
    """
    Analyze a text chunk through the AI agent pipeline.
    Returns speech metrics, audience reaction, cultural flags, coaching tip, and feedback.
    """
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
        events.append(event)
    return {"events": events}
