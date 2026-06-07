import os
import json
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from dotenv import load_dotenv

load_dotenv()

PERSONAS = {
    "investor": {
        "name": "Sarah Chen",
        "role": "Series A Investor",
        "location": "New York",
        "style": "data-driven, skeptical, direct"
    },
    "executive": {
        "name": "Marcus Webb",
        "role": "Chief Executive Officer",
        "location": "London",
        "style": "strategic, time-conscious, outcome-focused"
    },
    "recruiter": {
        "name": "Priya Nair",
        "role": "Senior Talent Partner",
        "location": "Singapore",
        "style": "evaluative, structured, competency-focused"
    },
    "customer": {
        "name": "Elena Russo",
        "role": "Head of Procurement",
        "location": "Milan",
        "style": "value-focused, cautious, detail-oriented"
    },
}

PROMPT = '''You are {name}, a {role} in {location}. Style: {style}.
Presenter just said: "{text}"
React as {name} in a real meeting. Return JSON only:
{{"reaction_type":"nodding|skeptical|distracted|engaged|interrupting","body_language":"one short phrase","internal_thought":"one sentence","would_ask":"question or null","focus_area":"{focus_area}"}}'''

def _build_kernel():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(
        service_id="groq",
        ai_model_id="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    ))
    return kernel

async def simulate_audience(
    text: str,
    persona: str = "investor",
    focus_area: str = "finance"
) -> dict:
    p = PERSONAS.get(persona, PERSONAS["investor"])
    kernel = _build_kernel()
    prompt = PROMPT.format(
        name=p["name"],
        role=p["role"],
        location=p["location"],
        style=p["style"],
        text=text[:200],
        focus_area=focus_area
    )
    try:
        result = await kernel.invoke_prompt(prompt)
        raw = str(result).strip()
        clean = raw.replace("`json","").replace("`","").strip()
        payload = json.loads(clean)
    except Exception:
        payload = {
            "reaction_type": "engaged",
            "body_language": "nodding slowly",
            "internal_thought": "Processing what was said.",
            "would_ask": None,
            "focus_area": focus_area
        }
    payload["speaker"] = p["name"]
    payload["role"] = p["role"]
    return {"agent": "audience", "type": "audience", "payload": payload}
