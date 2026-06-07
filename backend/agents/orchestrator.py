import asyncio
import time
from dataclasses import dataclass, field
from agents.speech import analyze_speech
from agents.audience import simulate_audience
from agents.coaching import get_coaching_tip
from agents.cultural import check_cultural_fit

@dataclass
class SessionContext:
    session_id: str
    persona: str = "investor"
    region: str = "us"
    focus_area: str = "finance"
    last_tip: str = "none"
    last_reaction: str = "neutral"
    start_time: float = field(default_factory=time.time)
    word_count: int = 0

    def elapsed(self) -> float:
        return time.time() - self.start_time

class Orchestrator:
    def __init__(self):
        self.context: SessionContext | None = None

    def configure(
        self,
        session_id: str,
        persona: str,
        region: str,
        focus_area: str
    ):
        self.context = SessionContext(
            session_id=session_id,
            persona=persona,
            region=region,
            focus_area=focus_area
        )

    async def process(self, text: str):
        if not self.context:
            return

        ctx = self.context

        # Speech — pure Python, runs first and fast
        speech_event = analyze_speech(text, ctx.elapsed())
        speech_event["session_id"] = ctx.session_id
        yield speech_event

        scores = speech_event["payload"]
        ctx.word_count += scores["word_count"]

        # Audience + Cultural run in parallel
        audience_task = asyncio.create_task(
            simulate_audience(text, ctx.persona, ctx.focus_area)
        )
        cultural_task = asyncio.create_task(
            check_cultural_fit(text, ctx.region, ctx.persona, ctx.focus_area)
        )

        audience_event, cultural_event = await asyncio.gather(
            audience_task, cultural_task
        )

        audience_event["session_id"] = ctx.session_id
        cultural_event["session_id"] = ctx.session_id

        ctx.last_reaction = audience_event["payload"].get("reaction_type", "neutral")

        yield audience_event
        yield cultural_event

        # Coaching runs last — uses speech + audience results
        coaching_event = await get_coaching_tip(
            scores, ctx.last_reaction, ctx.last_tip
        )
        coaching_event["session_id"] = ctx.session_id
        ctx.last_tip = coaching_event["payload"].get("tip", "none")

        yield coaching_event
