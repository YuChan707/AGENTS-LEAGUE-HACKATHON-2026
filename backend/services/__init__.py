"""
BACKEND SERVICES — Business logic and infrastructure adapters.

  llm_factory.py       — Groq (primary) / Azure OpenAI (fallback) LLM client
  blob_service.py      — Azure Blob Storage: uploads PPTX reports per session
  chroma_service.py    — ChromaDB vector store: cultural norms similarity search
  document_service.py  — extracts text from PPTX / DOCX / PDF uploads
  ingestion_service.py — stores analytics events in SQLite/PostgreSQL
  email_service.py     — drafts and sends follow-up email with session summary
  pptx_generator.py    — generates downloadable PPTX report from session data

Services are imported directly by agents/ and routes/ — they have no
knowledge of HTTP or WebSocket and contain no FastAPI code.
"""
