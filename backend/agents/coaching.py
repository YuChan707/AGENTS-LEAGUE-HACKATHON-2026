import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from dotenv import load_dotenv

load_dotenv()

PROMPT = """Presentation coach. Session data:
pace={pace}wpm fillers={fillers} clarity={clarity}/1.0 audience={audience}
Last tip given: {last_tip}

Give ONE coaching tip, max 12 words. Plain text only. No JSON. No punctuation at end."""

def _build_kernel():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(
        service_id="groq",
        ai_model_id="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    ))
    return kernel

def _sanitize(tip: str) -> str:
    tip = tip.split(".")[0].strip()
    words = tip.split()
    if len(words) > 15:
        tip = " ".join(words[:12]) + "..."
    if tip.lower().startswith("i "):
        return "Try pausing — let the audience absorb your point"
    return tip

async def get_coaching_tip(
    scores: dict,
    audience_reaction: str = "neutral",
    last_tip: str = "none"
) -> dict:
    kernel = _build_kernel()
    prompt = PROMPT.format(
        pace=scores.get("pace_wpm", 0),
        fillers=scores.get("filler_count", 0),
        clarity=scores.get("clarity_score", 0.0),
        audience=audience_reaction,
        last_tip=last_tip
    )
    try:
        result = await kernel.invoke_prompt(prompt)
        tip = _sanitize(str(result).strip())
    except Exception:
        tip = "Keep going — you are doing well"

    return {
        "agent": "coaching",
        "type": "coaching",
        "payload": {"tip": tip}
    }
