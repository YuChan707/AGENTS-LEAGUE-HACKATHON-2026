
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from services.chroma_service import chroma

def _build_kernel():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(
        service_id="groq",
        ai_model_id="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    ))
    return kernel

CULTURAL_PROMPT = """Cross-cultural communication expert.
Presenter context: {region} region, {persona} audience, {focus_area} focus.

Relevant cultural norms:
{norms}

Presenter just said: "{text}"

Does this statement risk cultural misalignment?
Return JSON only — no explanation outside JSON:
{{"flag": true, "issue": "brief description", "fix": "one-sentence suggestion"}}
or
{{"flag": false}}"""


async def check_cultural_fit(
    text: str,
    region: str,
    persona: str,
    focus_area: str
) -> dict:
    # 1. Retrieve relevant norms from ChromaDB
    norms = chroma.query(region, persona, focus_area, text)

    # If no norms found above threshold — no flag
    if not norms:
        return {"flag": False}

    norms_text = "\n".join(f"- {n}" for n in norms)

    # 2. Ask Llama to evaluate
    kernel = _build_kernel()
    prompt = CULTURAL_PROMPT.format(
        region=region,
        persona=persona,
        focus_area=focus_area,
        norms=norms_text,
        text=text[:200]     # truncate to keep tokens low
    )

    result = await kernel.invoke_prompt(prompt)
    raw = str(result).strip()

    # 3. Parse response safely
    try:
        import json
        # Strip any accidental markdown fences
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception:
        return {"flag": False}