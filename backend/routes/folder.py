"""
Folder-based document ingestion route.

POST /folder/scan   — list PPTX/DOCX/PDF files in a local directory
POST /folder/ingest — extract text + run AI analysis on each file
"""
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

from services.document_service import extract_text_from_path
from agents.document_analyst import analyze_document

router = APIRouter(prefix="/folder", tags=["folder"])

SUPPORTED = {".pptx", ".docx", ".pdf"}


class FolderRequest(BaseModel):
    folder_path: str
    persona_type: str = "executive"
    region: str = "us"
    focus_area: str = "business"
    environment: str = "professional"
    complexity: str = "medium"
    feedback_setting: str = "academic_us"
    audience_min_age: int = 18
    audience_max_age: int = 45
    audience_amount: int = 100


@router.post("/scan")
async def scan_folder(req: FolderRequest):
    path = Path(req.folder_path).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        return {"error": f"Folder not found: {req.folder_path}", "files": [], "file_count": 0}
    files = [
        {
            "name": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "path": str(f),
            "ext": f.suffix.lower().lstrip("."),
        }
        for f in sorted(path.iterdir())
        if f.is_file() and f.suffix.lower() in SUPPORTED
    ]
    return {
        "folder_name": path.name,
        "folder_path": str(path),
        "file_count": len(files),
        "files": files,
    }


@router.post("/ingest")
async def ingest_folder(req: FolderRequest):
    path = Path(req.folder_path).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        return {"error": f"Folder not found: {req.folder_path}", "results": [], "processed": 0, "errors": 1}

    folder_name = path.name
    results = []

    for file_path in sorted(path.iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED:
            continue
        try:
            text = await extract_text_from_path(str(file_path))
            doc_result = await analyze_document(
                text=text,
                persona=req.persona_type,
                focus_area=req.focus_area,
                environment=req.environment,
                complexity=req.complexity,
                region=req.region,
                min_age=req.audience_min_age,
                max_age=req.audience_max_age,
                amount=req.audience_amount,
            )
            results.append({
                "filename": file_path.name,
                "folder": folder_name,
                "word_count": len(text.split()),
                "status": "success",
                "analysis": doc_result["payload"],
            })
        except Exception as exc:
            results.append({
                "filename": file_path.name,
                "folder": folder_name,
                "status": "error",
                "error": str(exc),
            })

    processed = sum(1 for r in results if r["status"] == "success")
    return {
        "folder_name": folder_name,
        "folder_path": str(path),
        "processed": processed,
        "errors": len(results) - processed,
        "results": results,
    }
