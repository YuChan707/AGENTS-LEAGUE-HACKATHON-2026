import os
import json
from groq import AsyncGroq
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
Setting: {environment} presentation, content complexity is {complexity}.
Presenter just said: "{text}"
React as {name} in a real meeting. Return JSON only:
{{"reaction_type":"nodding|skeptical|distracted|engaged|interrupting","body_language":"one short phrase","internal_thought":"one sentence","would_ask":"question or null","focus_area":"{focus_area}"}}'''


async def simulate_audience(
    text: str,
    persona: str = "investor",
    focus_area: str = "finance",
    environment: str = "professional",
    complexity: str = "medium",
) -> dict:
    p = PERSONAS.get(persona, PERSONAS["investor"])
    prompt = PROMPT.format(
        name=p["name"],
        role=p["role"],
        location=p["location"],
        style=p["style"],
        text=text[:200],
        focus_area=focus_area,
        environment=environment,
        complexity=complexity,
    )
    try:
        client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        raw = response.choices[0].message.content.strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        payload = json.loads(clean)
    except Exception:
        payload = {
            "reaction_type": "engaged",
            "body_language": "nodding slowly",
            "internal_thought": "Processing what was said.",
            "would_ask": None,
            "focus_area": focus_area,
        }
    payload["speaker"] = p["name"]
    payload["role"] = p["role"]
    return {"agent": "audience", "type": "audience", "payload": payload}
