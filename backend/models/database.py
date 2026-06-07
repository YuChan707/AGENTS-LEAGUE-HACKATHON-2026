import os, uuid, ssl
from pathlib import Path
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Explicitly resolve .env from project root regardless of working directory
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path, override=True)

Base = declarative_base()

DATABASE_URL = (
    os.getenv("DATABASE_POOL_URL")
    or os.getenv("DATABASE_URL")
    or "sqlite+aiosqlite:///./onlooker.db"
)
_sqlite = DATABASE_URL.startswith("sqlite")

if _sqlite:
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"ssl": ssl_context},
        pool_size=5,
        max_overflow=10,
        echo=False,
    )

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


class AudienceModel(Base):
    __tablename__ = "audiences"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_type = Column(String, nullable=False)
    region = Column(String, nullable=False)
    focus_area = Column(String, nullable=False)
    demographic_data = Column(JSON)
    behavioral_profile = Column(JSON)
    group_label = Column(String)
    group_size_estimate = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class SessionModel(Base):
    __tablename__ = "sessions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    audience_id = Column(String(36))
    persona_type = Column(String, nullable=False)
    region = Column(String, nullable=False)
    focus_area = Column(String, nullable=False)
    status = Column(String, default="active")
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))


class AnalyticModel(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    engagement_level = Column(Float, default=0.0)
    sentiment_score = Column(Float, default=0.0)
    attention_score = Column(Float, default=0.0)
    conviction_level = Column(Float, default=0.0)
    objection_count = Column(Integer, default=0)
    decision_readiness = Column(Float, default=0.0)
    risk_perception = Column(Float, default=0.0)
    pace_wpm = Column(Integer, default=0)
    filler_count = Column(Integer, default=0)
    clarity_score = Column(Float, default=0.0)


class IngestionEventModel(Base):
    __tablename__ = "ingestion_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36))
    source = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    raw_payload = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    ingested_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ReportModel(Base):
    __tablename__ = "reports"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False)
    report_type = Column(String, nullable=False)
    summary = Column(JSON)
    file_url = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
