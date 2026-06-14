import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()
from models.database import AsyncSessionLocal, init_db, AudienceModel
from data_processor.build_profiles import run as get_profiles

async def seed():
    await init_db()
    profiles = await get_profiles()
    async with AsyncSessionLocal() as db:
        for p in profiles:
            audience = AudienceModel(**p)
            db.add(audience)
        await db.commit()
    print(f"Seeded {len(profiles)} audience profiles into database.")

if __name__ == "__main__":
    asyncio.run(seed())
