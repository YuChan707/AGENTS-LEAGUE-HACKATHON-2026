
from services.chroma_service import chroma

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    chroma.seed()           # ← add this line
    print("Database and ChromaDB ready")
    yield