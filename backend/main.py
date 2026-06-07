"""FastAPI entry point.

Wires up the application: lifespan (startup/shutdown), CORS, and routers
(health, session, stream). This is the module uvicorn runs:

    uvicorn backend.main:app --reload

TODO (scaffold): create the FastAPI app, register routers from
backend.routes, and open/close shared resources (DB engine, ChromaDB client)
inside the lifespan context manager.
"""

# from contextlib import asynccontextmanager
# from fastapi import FastAPI
# from backend.routes import health, session, stream


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # startup: init DB, seed ChromaDB, ...
#     yield
#     # shutdown: close clients


# app = FastAPI(title="OnLooker", lifespan=lifespan)
# app.include_router(health.router)
# app.include_router(session.router)
# app.include_router(stream.router)
