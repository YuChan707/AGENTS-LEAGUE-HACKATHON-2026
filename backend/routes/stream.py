import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from agents.orchestrator import Orchestrator
from agents.vision import analyze_frame
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
                    focus_area=data.get("focus_area", "finance"),
                    environment=data.get("environment", "professional"),
                    complexity=data.get("complexity", "medium"),
                    feedback_setting=data.get("feedback_setting", "academic_us"),
                    audience_min_age=int(data.get("audience_min_age", 18)),
                    audience_max_age=int(data.get("audience_max_age", 45)),
                    audience_amount=int(data.get("audience_amount", 100)),
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

            elif data.get("type") == "video_frame":
                image_b64 = data.get("image_base64", "").strip()
                if image_b64 and orchestrator.context:
                    ctx = orchestrator.context
                    visual_event = await analyze_frame(
                        image_b64,
                        ctx.persona,
                        ctx.focus_area,
                        ctx.environment,
                        ctx.complexity,
                    )
                    visual_event["session_id"] = ctx.session_id
                    await websocket.send_json(visual_event)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "agent": "system",
                "message": str(e)
            })
        except Exception:
            pass
