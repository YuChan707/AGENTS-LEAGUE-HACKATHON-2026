"""WebSocket streaming route.

Exposes WS /ws/stream: receives live speech/transcript chunks from the
frontend, fans them out through the agent orchestrator, and pushes agent
results (scores, coaching tips, audience reactions, cultural flags) back to
the client in real time.

TODO (scaffold): create the APIRouter, accept the WebSocket connection, and
loop on receive -> orchestrator.run(...) -> send.
"""

# from fastapi import APIRouter, WebSocket

# router = APIRouter()


# @router.websocket("/ws/stream")
# async def stream(ws: WebSocket):
#     await ws.accept()
#     ...
