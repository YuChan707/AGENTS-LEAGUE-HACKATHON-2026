"""SQLAlchemy models + engine + get_db dependency.

Holds the ORM table definitions for OnLooker (sessions, raw events,
analytics records), the SQLAlchemy engine/sessionmaker, and the `get_db`
FastAPI dependency that yields a scoped session per request.

TODO (scaffold): define Base, engine, SessionLocal, the ORM models, and
the get_db() generator.
"""

# from sqlalchemy import create_engine
# from sqlalchemy.orm import declarative_base, sessionmaker

# Base = declarative_base()
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
