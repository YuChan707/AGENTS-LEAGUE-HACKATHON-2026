
import asyncio
from services.ingestion_service import DataIngestionService
from services.email_service import generate_email_draft
from services.pptx_generator import generate_onlooker_report
from services.blob_service import blob_storage
from models.database import ReportModel

ingestion_svc = DataIngestionService()

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
        return {"error": "Session not found"}

    # Build summary from analytics
    analytics = await ingestion_svc.get_session_analytics(str(session_id))
    summary = {
        "session_id": str(session_id),
        "persona_type": session.persona_type,
        "region": session.region,
        "focus_area": session.focus_area,
        "analytics": analytics,
        "audience_groups": []   # populated by group identification agent
    }

    # Run PPTX + email in parallel
    pptx_bytes, email_data = await asyncio.gather(
        asyncio.to_thread(generate_onlooker_report, summary),
        generate_email_draft(summary)
    )

    # Upload PPTX to Azure Blob
    pptx_url = await blob_storage.upload_pptx(pptx_bytes, str(session_id))

    # Also archive session summary JSON
    await blob_storage.upload_json(summary, str(session_id), "session_summary")

    # Save report record
    report = ReportModel(
        session_id=session_id,
        report_type="full",
        summary={**summary, "email": email_data},
        file_url=pptx_url
    )
    db.add(report)
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    await db.commit()

    return {
        "session_id": str(session_id),
        "status": "completed",
        "pptx_url": pptx_url,
        "email": email_data
    }