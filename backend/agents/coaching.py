from services.llm_factory import get_llm_client, get_model

PROMPT = """Presentation coach. Session data:
pace={pace}wpm fillers={fillers} clarity={clarity}/1.0 audience={audience}
Setting: {environment} presentation, content complexity: {complexity}
Audience: {audience_amount} attendees, age group {audience_min_age}–{audience_max_age}
Last tip given: {last_tip}

If there is not enough context (very short input, first words only), respond with exactly:
"Need more context to coach"

Otherwise give ONE coaching tip tailored to the setting, complexity, and audience, max 12 words. Plain text only. No JSON. No punctuation at end."""


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
    last_tip: str = "none",
    environment: str = "professional",
    complexity: str = "medium",
    audience_min_age: int = 18,
    audience_max_age: int = 45,
    audience_amount: int = 100,
) -> dict:
    word_count = scores.get("word_count", 0)

    if word_count < 5:
        return {"agent": "coaching", "type": "coaching", "payload": {"tip": ""}}

    prompt = PROMPT.format(
        pace=scores.get("pace_wpm", 0),
        fillers=scores.get("filler_count", 0),
        clarity=scores.get("clarity_score", 0.0),
        audience=audience_reaction,
        last_tip=last_tip,
        environment=environment,
        complexity=complexity,
        audience_min_age=audience_min_age,
        audience_max_age=audience_max_age,
        audience_amount=audience_amount,
    )
    try:
        client = get_llm_client()
        response = await client.chat.completions.create(
            model=get_model(fast=True),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.5,
        )
        tip = _sanitize(response.choices[0].message.content.strip())
        if not tip or tip.lower() in ("need more context to coach", ""):
            tip = ""
    except Exception:
        tip = "Keep going — you are doing well"

    return {"agent": "coaching", "type": "coaching", "payload": {"tip": tip}}
