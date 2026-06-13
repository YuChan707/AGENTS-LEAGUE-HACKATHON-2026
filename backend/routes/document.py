from fastapi import APIRouter, File, Form, UploadFile
from agents.orchestrator import Orchestrator
from services.document_service import extract_text

router = APIRouter(tags=["document"])


@router.post("/document/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form("chat"),
    persona_type: str = Form("executive"),
    region: str = Form("us"),
    focus_area: str = Form("business"),
    environment: str = Form("professional"),
    complexity: str = Form("medium"),
    analyze: bool = Form(False),
):
    """
    Upload a .pptx, .docx, or .pdf file.

    Returns the extracted text and, if analyze=true, runs it through the AI
    agent pipeline and returns agent events alongside the text.
    """
    text = await extract_text(file)
    word_count = len(text.split())

    if not analyze:
        return {
            "filename": file.filename,
            "text": text,
            "word_count": word_count,
        }

    orch = Orchestrator()
    orch.configure(
        session_id=session_id,
        persona=persona_type,
        region=region,
        focus_area=focus_area,
        environment=environment,
        complexity=complexity,
    )
    events: list[dict] = []
    async for event in orch.process(text[:2000]):  # cap to avoid token overrun
        events.append(event)

    return {
        "filename": file.filename,
        "text": text,
        "word_count": word_count,
        "events": events,
    }
