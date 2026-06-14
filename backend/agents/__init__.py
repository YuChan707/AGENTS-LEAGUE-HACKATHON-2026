"""
AGENT SECTION — AI pipeline that processes presentation data in real time.

  orchestrator.py      — coordinates all agents for each incoming event
  speech.py            — pace, filler words, clarity scoring from transcript
  audience.py          — simulates audience persona reactions and questions
  coaching.py          — generates real-time coaching tips
  cultural.py          — cross-cultural communication check via ChromaDB
  feedback.py          — segment-level feedback aggregation
  vision.py            — screen-frame analysis (slide content, visuals)
  document_analyst.py  — full-document deep analysis (structure, engagement)

Agents receive events from routes/stream.py (WebSocket) and write results
back through the same socket so the frontend AliveModeView can update live.
"""
