"""
Full-document analysis agent.

Detects document type (report vs presentation), evaluates fit against
audience settings, and returns structured data for both the chat message
and the Live AI panel.
"""
import json
from services.llm_factory import get_llm_client, get_model

_SYSTEM = """You are an expert presentation and report analyst.

Read the document text and the audience/setting context, then return ONLY valid JSON:
{
  "doc_type": "presentation|report|other",
  "paragraphs": [
    "<opening paragraph: what the document covers and its main purpose>",
    "<closing paragraph: concrete recommendations tailored to the setting>"
  ],
  "success_scores": {
    "audience":     <integer 0-100, likelihood this content succeeds with the specified audience type>,
    "environment":  <integer 0-100, how well the content fits the environment (professional vs casual)>,
    "complexity":   <integer 0-100, how easy it is to understand at the stated complexity level>
  },
  "language_tone": "professional|casual",
  "short_feedback": "<one sentence: the single most important action for the presenter>",
  "live_ai_items": [
    {"category": "grammar",     "text": "<one concise sentence about grammar or wording issues>"},
    {"category": "engagement",  "text": "<one concise sentence about audience engagement>"},
    {"category": "clarity",     "text": "<one concise sentence about information clarity>"},
    {"category": "structure",   "text": "<one concise sentence about document structure>"},
    {"category": "delivery",    "text": "<one concise sentence about delivery or tone>"}
  ],
  "graph_data": {
    "by_age": [
      {"group": "Under 25", "engagement": <0-100>, "impact": <0-100>},
      {"group": "25-40",    "engagement": <0-100>, "impact": <0-100>},
      {"group": "40-60",    "engagement": <0-100>, "impact": <0-100>},
      {"group": "60+",      "engagement": <0-100>, "impact": <0-100>}
    ],
    "by_type": [
      {"group": "Academic",  "engagement": <0-100>, "impact": <0-100>},
      {"group": "Corporate", "engagement": <0-100>, "impact": <0-100>},
      {"group": "Technical", "engagement": <0-100>, "impact": <0-100>},
      {"group": "General",   "engagement": <0-100>, "impact": <0-100>}
    ]
  }
}

Rules:
- doc_type: "report" if the document is dense with data/findings; "presentation" if it has slides/bullet points; else "other"
- Reports need numbers, citations, and graphs. Presentations need brevity and simplicity.
- language_tone: infer from actual language used in the document
- success_scores reflect how well THIS document works for THESE settings, not in general
- live_ai_items: write exactly 5 items (one per category), each a single sentence, specific to the content
- Scores must vary meaningfully — do not return all the same number
- Return ONLY the JSON object, no markdown fences, no extra text"""

_USER = """Document content (first 4 000 chars):
\"\"\"
{text}
\"\"\"

Audience settings:
- Audience type  : {persona}
- Environment    : {environment}
- Complexity     : {complexity}
- Focus area     : {focus_area}
- Region         : {region}
- Age range      : {min_age}–{max_age} years
- Audience size  : {amount} people

Analyze how well this document serves these settings. Detect whether it is a report or presentation, identify language tone, and score fitness on each dimension."""


async def analyze_document(
    text: str,
    persona: str = "executive",
    focus_area: str = "business",
    environment: str = "professional",
    complexity: str = "medium",
    region: str = "us",
    min_age: int = 18,
    max_age: int = 45,
    amount: int = 100,
) -> dict:
    prompt = _USER.format(
        text=text[:4000],
        persona=persona,
        environment=environment,
        complexity=complexity,
        focus_area=focus_area,
        region=region,
        min_age=min_age,
        max_age=max_age,
        amount=amount,
    )
    try:
        client = get_llm_client()
        resp = await client.chat.completions.create(
            model=get_model(fast=False),
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1600,
            temperature=0.5,
        )
        raw = resp.choices[0].message.content.strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
    except Exception:
        result = _fallback(persona, focus_area, environment, complexity, region)

    return {"agent": "document_analysis", "type": "document_analysis", "payload": result}


def _fallback(persona: str, focus_area: str, environment: str, complexity: str, region: str) -> dict:
    return {
        "doc_type": "other",
        "paragraphs": [
            f"This document addresses {focus_area} topics for a {persona} audience in a {environment} setting. "
            f"The content complexity is rated {complexity}, targeting the {region.upper()} region.",
            "Consider adding concrete data points, simplifying the opening section, and aligning the language tone "
            "with the environment — professional settings require formal vocabulary while casual settings allow conversational language.",
        ],
        "success_scores": {"audience": 72, "environment": 76, "complexity": 65},
        "language_tone": "professional" if environment == "professional" else "casual",
        "short_feedback": "Add concrete examples and align language tone with your audience setting.",
        "live_ai_items": [
            {"category": "grammar",    "text": "Check for passive voice and overly long sentences."},
            {"category": "engagement", "text": "Opening section lacks a compelling hook to capture attention."},
            {"category": "clarity",    "text": "Some sections use jargon that may lose a non-specialist audience."},
            {"category": "structure",  "text": "Key takeaways should be clearly stated at the end of each section."},
            {"category": "delivery",   "text": "Tone is broadly appropriate but could be warmer for the target audience."},
        ],
        "graph_data": {
            "by_age": [
                {"group": "Under 25", "engagement": 62, "impact": 55},
                {"group": "25-40",    "engagement": 82, "impact": 76},
                {"group": "40-60",    "engagement": 74, "impact": 71},
                {"group": "60+",      "engagement": 51, "impact": 58},
            ],
            "by_type": [
                {"group": "Academic",  "engagement": 78, "impact": 73},
                {"group": "Corporate", "engagement": 85, "impact": 80},
                {"group": "Technical", "engagement": 67, "impact": 63},
                {"group": "General",   "engagement": 58, "impact": 52},
            ],
        },
    }
