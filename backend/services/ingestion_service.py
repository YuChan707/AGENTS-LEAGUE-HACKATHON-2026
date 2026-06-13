import asyncio
from datetime import datetime
from models.database import AsyncSessionLocal, IngestionEventModel, AnalyticModel

class DataIngestionService:
    async def ingest(self, event: dict) -> None:
        async with AsyncSessionLocal() as db:
            raw = IngestionEventModel(
                session_id=event.get("session_id"),
                source=event.get("agent", "unknown"),
                event_type=event.get("type", "unknown"),
                raw_payload=event.get("payload", {}),
                processed=False
            )
            db.add(raw)
            await db.commit()
            await db.refresh(raw)
        asyncio.create_task(self._process(raw.id, event))

    async def _process(self, event_id: int, event: dict) -> None:
        async with AsyncSessionLocal() as db:
            p = event.get("payload", {})
            analytic = AnalyticModel(
                session_id=event.get("session_id"),
                recorded_at=datetime.utcnow(),
                pace_wpm=p.get("pace_wpm", 0),
                filler_count=p.get("filler_count", 0),
                clarity_score=p.get("clarity_score", 0.0),
                engagement_level=p.get("engagement", 0.0),
                sentiment_score=p.get("sentiment", 0.0),
                attention_score=p.get("attention", 0.0),
                conviction_level=p.get("conviction", 0.0),
                objection_count=p.get("objections", 0),
                decision_readiness=p.get("readiness", 0.0),
                risk_perception=p.get("risk", 0.0),
            )
            db.add(analytic)
            raw = await db.get(IngestionEventModel, event_id)
            if raw:
                raw.processed = True
            await db.commit()

    async def get_session_analytics(self, session_id: str) -> dict:
        from sqlalchemy import select, func
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(
                    func.avg(AnalyticModel.engagement_level).label("engagement_level"),
                    func.avg(AnalyticModel.sentiment_score).label("sentiment_score"),
                    func.avg(AnalyticModel.conviction_level).label("conviction_level"),
                    func.avg(AnalyticModel.clarity_score).label("clarity_score"),
                    func.avg(AnalyticModel.pace_wpm).label("pace_wpm"),
                    func.sum(AnalyticModel.filler_count).label("filler_count"),
                ).where(AnalyticModel.session_id == session_id)
            )
            row = result.one_or_none()
            if not row:
                return {}
            return {k: round(float(v or 0), 2) for k, v in row._mapping.items()}

ingestion_service = DataIngestionService()
