"""Speech agent (no LLM).

Computes objective delivery metrics from the transcript/audio chunk:
speaking pace (wpm), filler-word count, and clarity. Pure heuristics, no
model calls, so it can run on every chunk cheaply.

TODO (scaffold): implement analyze(event) -> {pace, fillers, clarity}.
"""

# async def analyze(event):
#     ...
