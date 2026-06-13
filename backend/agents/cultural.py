import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

PROMPT = """Cross-cultural communication expert.
Context: {region} region, {persona} audience, {focus_area} focus.
Relevant norms:
{norms}
Presenter said: "{text}"
Cultural mismatch? Return JSON only:
{{"flag":true,"issue":"brief description","fix":"one sentence suggestion"}}
or {{"flag":false}}"""


async def check_cultural_fit(
    text: str,
    region: str = "us",
    persona: str = "investor",
    focus_area: str = "finance",
    norms: list[str] | None = None,
) -> dict:
    if not norms:
        return {"agent": "cultural", "type": "cultural", "payload": {"flag": False}}

    norms_text = "\n".join(f"- {n}" for n in norms[:2])
    prompt = PROMPT.format(
        region=region,
        persona=persona,
        focus_area=focus_area,
        norms=norms_text,
        text=text[:200],
    )
    try:
        client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        payload = json.loads(clean)
    except Exception:
        payload = {"flag": False}

    return {"agent": "cultural", "type": "cultural", "payload": payload}
