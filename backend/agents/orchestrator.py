import asyncio
import time
from dataclasses import dataclass, field
from agents.speech import analyze_speech
from agents.audience import simulate_audience
from agents.coaching import get_coaching_tip
from agents.cultural import check_cultural_fit
from agents.feedback import simulate_feedback
from services.chroma_service import chroma

@dataclass
class SessionContext:
    session_id: str
    persona: str = "investor"
    region: str = "us"
    focus_area: str = "finance"
    environment: str = "professional"
    complexity: str = "medium"
    feedback_setting: str = "academic_us"
    audience_min_age: int = 18
    audience_max_age: int = 45
    audience_amount: int = 100
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
        focus_area: str,
        environment: str = "professional",
        complexity: str = "medium",
        feedback_setting: str = "academic_us",
        audience_min_age: int = 18,
        audience_max_age: int = 45,
        audience_amount: int = 100,
    ):
        self.context = SessionContext(
            session_id=session_id,
            persona=persona,
            region=region,
            focus_area=focus_area,
            environment=environment,
            complexity=complexity,
            feedback_setting=feedback_setting,
            audience_min_age=audience_min_age,
            audience_max_age=audience_max_age,
            audience_amount=audience_amount,
        )

    async def process(self, text: str):
        if not self.context:
            return

        ctx = self.context
        words = text.strip().split()

        # Guard: too little text to feed to AI agents — silently skip, no error event
        if len(words) < 5:
            return

        # Speech — pure Python, runs first and fast
        speech_event = analyze_speech(text, ctx.elapsed())
        speech_event["session_id"] = ctx.session_id
        yield speech_event

        scores = speech_event["payload"]
        ctx.word_count += scores["word_count"]

        # Query ChromaDB for cultural norms before running cultural agent
        norms = chroma.query(ctx.region, ctx.persona, ctx.focus_area, text)

        # Audience + Cultural + Feedback run in parallel
        audience_task = asyncio.create_task(
            simulate_audience(text, ctx.persona, ctx.focus_area, ctx.environment, ctx.complexity, ctx.audience_min_age, ctx.audience_max_age, ctx.audience_amount)
        )
        cultural_task = asyncio.create_task(
            check_cultural_fit(text, ctx.region, ctx.persona, ctx.focus_area, norms)
        )
        feedback_task = asyncio.create_task(
            simulate_feedback(text, ctx.feedback_setting, ctx.complexity, ctx.environment)
        )

        audience_event, cultural_event, feedback_event = await asyncio.gather(
            audience_task, cultural_task, feedback_task
        )

        audience_event["session_id"] = ctx.session_id
        cultural_event["session_id"] = ctx.session_id
        feedback_event["session_id"] = ctx.session_id

        ctx.last_reaction = audience_event["payload"].get("reaction_type", "neutral")

        yield audience_event
        yield cultural_event
        yield feedback_event

        # Coaching runs last — uses speech + audience results
        coaching_event = await get_coaching_tip(
            scores, ctx.last_reaction, ctx.last_tip, ctx.environment, ctx.complexity, ctx.audience_min_age, ctx.audience_max_age, ctx.audience_amount
        )
        tip = coaching_event["payload"].get("tip", "")
        if tip:
            coaching_event["session_id"] = ctx.session_id
            ctx.last_tip = tip
            yield coaching_event
