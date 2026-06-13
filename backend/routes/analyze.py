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


@router.post("/analyze/chunk")
async def analyze_chunk(req: ChunkRequest):
    """
    Analyze a text chunk through the AI agent pipeline.
    Returns speech metrics, audience reaction, cultural flags, and coaching tip.
    """
    orch = Orchestrator()
    orch.configure(
        session_id=req.session_id,
        persona=req.persona_type,
        region=req.region,
        focus_area=req.focus_area,
        environment=req.environment,
        complexity=req.complexity,
    )
    events: list[dict] = []
    async for event in orch.process(req.text):
        events.append(event)
    return {"events": events}
