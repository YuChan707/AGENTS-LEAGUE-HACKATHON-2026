from fastapi import APIRouter, File, Form, UploadFile
from agents.orchestrator import Orchestrator
from agents.document_analyst import analyze_document
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
    feedback_setting: str = Form("academic_us"),
    audience_min_age: int = Form(18),
    audience_max_age: int = Form(45),
    audience_amount: int = Form(100),
    analyze: bool = Form(False),
):
    """
    Upload a .pptx, .docx, or .pdf file.

    When analyze=true, runs two parallel analyses:
    - Agent pipeline (speech/audience/cultural/coaching) on the first 2 000 chars
    - Full document analysis returning paragraph + graph data + short feedback
    """
    text = await extract_text(file)
    word_count = len(text.split())

    if not analyze:
        return {"filename": file.filename, "text": text, "word_count": word_count}

    # Agent pipeline — chunk-level events
    orch = Orchestrator()
    orch.configure(
        session_id=session_id,
        persona=persona_type,
        region=region,
        focus_area=focus_area,
        environment=environment,
        complexity=complexity,
        feedback_setting=feedback_setting,
        audience_min_age=audience_min_age,
        audience_max_age=audience_max_age,
        audience_amount=audience_amount,
    )
    events: list[dict] = []
    async for event in orch.process(text[:2000]):
        events.append(event)

    # Full document analysis — runs on more text, returns paragraph + graph
    doc_analysis = await analyze_document(
        text=text,
        persona=persona_type,
        focus_area=focus_area,
        environment=environment,
        complexity=complexity,
        region=region,
        min_age=audience_min_age,
        max_age=audience_max_age,
        amount=audience_amount,
    )

    return {
        "filename": file.filename,
        "text": text,
        "word_count": word_count,
        "events": events,
        "document_analysis": doc_analysis["payload"],
    }
