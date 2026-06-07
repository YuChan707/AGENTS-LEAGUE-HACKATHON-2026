import os
import json
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
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

def _build_kernel():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(
        service_id="groq",
        ai_model_id="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    ))
    return kernel

async def check_cultural_fit(
    text: str,
    region: str = "us",
    persona: str = "investor",
    focus_area: str = "finance",
    norms: list[str] | None = None
) -> dict:
    if not norms:
        return {"agent": "cultural", "type": "cultural", "payload": {"flag": False}}

    norms_text = "\n".join(f"- {n}" for n in norms[:2])
    kernel = _build_kernel()
    prompt = PROMPT.format(
        region=region,
        persona=persona,
        focus_area=focus_area,
        norms=norms_text,
        text=text[:200]
    )
    try:
        result = await kernel.invoke_prompt(prompt)
        raw = str(result).strip()
        clean = raw.replace("`json","").replace("`","").strip()
        payload = json.loads(clean)
    except Exception:
        payload = {"flag": False}

    return {"agent": "cultural", "type": "cultural", "payload": payload}
