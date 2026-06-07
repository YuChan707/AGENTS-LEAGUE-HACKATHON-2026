"""Cultural agent.

Retrieves culturally-relevant context from ChromaDB (RAG) and asks a Llama
model whether the message risks a cultural mismatch for the target region,
raising a flag when it does.

TODO (scaffold): implement check(event) -> {flagged, reason, context}.
"""

# async def check(event):
#     ...
