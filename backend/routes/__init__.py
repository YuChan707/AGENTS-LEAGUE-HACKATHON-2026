"""
SELECTOR / ENDPOINTS — FastAPI routers that connect the frontend to the backend.

  health.py    — GET  /health                    liveness probe
  session.py   — CRUD /session/*                 session management + PPTX report
  stream.py    — WS   /ws/stream                 real-time agent event stream
  analyze.py   — POST /analyze/chunk             AI instruction chunk endpoint
  document.py  — POST /document/upload           upload PPTX/DOCX/PDF for analysis
  feedback.py  — GET/POST /feedback/*            audience feedback records

All routers are registered in backend/main.py via app.include_router().
The frontend (ui-onlooker/) connects through NEXT_PUBLIC_API_URL (HTTP)
and NEXT_PUBLIC_WS_URL (WebSocket).
"""
