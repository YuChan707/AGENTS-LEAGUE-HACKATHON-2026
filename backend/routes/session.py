"""Session routes.

Lifecycle of a practice/presentation session:
  - POST /session/start      -> create a session, return its id
  - GET  /session/{id}       -> fetch session state + analytics
  - POST /session/{id}/complete -> finalize, trigger report generation

TODO (scaffold): create the APIRouter and implement the handlers using the
get_db dependency and the dtos in dtos/.
"""

# from fastapi import APIRouter, Depends

# router = APIRouter(prefix="/session", tags=["session"])
