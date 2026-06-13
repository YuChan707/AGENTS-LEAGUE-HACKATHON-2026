from fastapi import APIRouter
from sqlalchemy import text
from models.database import AsyncSessionLocal

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:80]}"

    return {
        "status": "ok",
        "version": "0.1.0",
        "database": db_status
    }
