import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from agents.orchestrator import Orchestrator
from services.ingestion_service import ingestion_service

router = APIRouter(tags=["stream"])

@router.websocket("/ws/stream")
async def stream(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    orchestrator = Orchestrator()

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "init":
                orchestrator.configure(
                    session_id=session_id,
                    persona=data.get("persona", "investor"),
                    region=data.get("region", "us"),
                    focus_area=data.get("focus_area", "finance")
                )
                await websocket.send_json({
                    "type": "session_ready",
                    "session_id": session_id
                })

            elif data.get("type") == "transcript_chunk":
                text = data.get("text", "").strip()
                if not text:
                    continue
                async for event in orchestrator.process(text):
                    await ingestion_service.ingest(event)
                    await websocket.send_json(event)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
