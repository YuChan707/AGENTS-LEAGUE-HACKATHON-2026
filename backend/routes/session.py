import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db, SessionModel
from services.ingestion_service import ingestion_service
from services.pptx_generator import generate_onlooker_report
from services.blob_service import blob_storage
from services.email_service import generate_email_draft

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
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
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
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    await db.commit()
    return {
        "session_id": str(session_id),
        "status": "completed"
    }

@router.get("/{session_id}/analytics")
async def get_session_analytics(session_id: uuid.UUID):
    """Return aggregated metrics for a session."""
    data = await ingestion_service.get_session_analytics(str(session_id))
    if not data:
        raise HTTPException(status_code=404, detail="No analytics found for this session")
    return {"session_id": str(session_id), "analytics": data}

@router.post("/{session_id}/report")
async def generate_report(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Generate a PPTX report + email draft and return download URL."""
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    analytics = await ingestion_service.get_session_analytics(str(session_id))
    session_data = {
        "persona_type": session.persona_type,
        "region": session.region,
        "focus_area": session.focus_area,
        "analytics": analytics,
        "audience_groups": [],
    }

    pptx_bytes = generate_onlooker_report(session_data)
    pptx_url = await blob_storage.upload_pptx(pptx_bytes, str(session_id))

    email = await generate_email_draft(session_data)

    return {
        "session_id": str(session_id),
        "pptx_url": pptx_url,
        "pptx_available": pptx_url is not None,
        "email_draft": email,
    }

@router.get("/{session_id}/report/download")
async def download_report(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Generate and stream PPTX directly when Azure Blob is not configured."""
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    analytics = await ingestion_service.get_session_analytics(str(session_id))
    session_data = {
        "persona_type": session.persona_type,
        "region": session.region,
        "focus_area": session.focus_area,
        "analytics": analytics,
        "audience_groups": [],
    }
    pptx_bytes = generate_onlooker_report(session_data)
    filename = f"onlooker_report_{session_id}.pptx"
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
