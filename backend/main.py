import os, sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from models.database import init_db
from services.chroma_service import chroma
from routes.health import router as health_router
from routes.session import router as session_router
from routes.stream import router as stream_router
from routes.analyze import router as analyze_router
from routes.document import router as document_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Onlooker API...")
    await init_db()
    chroma.seed()
    print("Database + ChromaDB ready")
    yield
    print("Shutting down")

app = FastAPI(title="Onlooker API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(health_router)
app.include_router(session_router)
app.include_router(stream_router)
app.include_router(analyze_router)
app.include_router(document_router)
