
import os, asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import (
    AsyncSessionLocal,
    IngestionEventModel,
    AnalyticModel,
    AudienceModel
)

class DataIngestionService:
    """
    Receives raw agent events, writes them immediately,
    then processes them into analytics rows in the background.
    Never blocks the WebSocket stream.
    """

    async def ingest(self, event: dict) -> None:
        async with AsyncSessionLocal() as db:
            # 1. Write raw event immediately — never lose data
            raw = IngestionEventModel(
                session_id=event.get("session_id"),
                source=event.get("agent"),        # 'speech'|'audience'|'coaching'|'cultural'
                event_type=event.get("type"),
                raw_payload=event.get("payload", {}),
                processed=False
            )
            db.add(raw)
            await db.commit()
            await db.refresh(raw)

        # 2. Process into analytics — background, non-blocking
        asyncio.create_task(self._process(raw.id, event))

    async def _process(self, event_id: int, event: dict) -> None:
        async with AsyncSessionLocal() as db:
            payload = event.get("payload", {})
            agent   = event.get("agent", "")

            # Build analytic record from whatever agent fired
            analytic = AnalyticModel(
                session_id=event.get("session_id"),
                recorded_at=datetime.utcnow(),

                # Speech agent fields
                pace_wpm      = payload.get("pace_wpm", 0),
                filler_count  = payload.get("filler_count", 0),
                clarity_score = payload.get("clarity_score", 0.0),

                # Audience agent fields
                engagement_level = payload.get("engagement", 0.0),
                sentiment_score  = payload.get("sentiment", 0.0),
                attention_score  = payload.get("attention", 0.0),

                # Coaching agent fields
                conviction_level  = payload.get("conviction", 0.0),
                objection_count   = payload.get("objections", 0),
                decision_readiness= payload.get("readiness", 0.0),
                risk_perception   = payload.get("risk", 0.0),
            )
            db.add(analytic)

            # Mark raw event processed
            raw = await db.get(IngestionEventModel, event_id)
            if raw:
                raw.processed = True

            await db.commit()

    async def get_session_analytics(self, session_id: str) -> dict:
        """
        Aggregate analytics for a session — used by M365 report generator.
        Returns averaged metrics across all recorded events.
        """
        async with AsyncSessionLocal() as db:
            from sqlalchemy import func
            result = await db.execute(
                select(
                    func.avg(AnalyticModel.engagement_level).label("engagement_level"),
                    func.avg(AnalyticModel.sentiment_score).label("sentiment_score"),
                    func.avg(AnalyticModel.attention_score).label("attention_score"),
                    func.avg(AnalyticModel.conviction_level).label("conviction_level"),
                    func.sum(AnalyticModel.objection_count).label("objection_count"),
                    func.avg(AnalyticModel.decision_readiness).label("decision_readiness"),
                    func.avg(AnalyticModel.risk_perception).label("risk_perception"),
                    func.avg(AnalyticModel.pace_wpm).label("pace_wpm"),
                    func.sum(AnalyticModel.filler_count).label("filler_count"),
                    func.avg(AnalyticModel.clarity_score).label("clarity_score"),
                ).where(AnalyticModel.session_id == session_id)
            )
            row = result.one_or_none()
            if not row:
                return {}

            return {k: round(float(v or 0), 2) for k, v in row._mapping.items()}