
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db, SessionModel

router = APIRouter(prefix="/session", tags=["session"])

@router.post("/start")
async def start_session(
    persona_type: str = "investor",
    region: str = "us",
    focus_area: str = "finance",
    db: AsyncSession = Depends(get_db)
):
    session = SessionModel(
        persona_type=persona_type,
        region=region,
        focus_area=focus_area,
        status="active"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {
        "session_id": str(session.id),
        "status": "active",
        "started_at": session.started_at
    }

@router.get("/{session_id}")
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SessionModel).where(
            SessionModel.id == session_id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found"}
    return {
        "session_id": str(session.id),
        "persona_type": session.persona_type,
        "region": session.region,
        "focus_area": session.focus_area,
        "status": session.status
    }

@router.post("/{session_id}/complete")
async def complete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SessionModel).where(
            SessionModel.id == session_id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found"}
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    await db.commit()
    return {
        "session_id": str(session_id),
        "status": "completed"
    }