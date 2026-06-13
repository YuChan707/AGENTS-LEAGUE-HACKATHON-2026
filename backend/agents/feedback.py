import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

# Feedback personas based on location, culture, group type, and ethnicity
FEEDBACK_SETTINGS = {
    "academic_us": {
        "group": "academic",
        "location": "United States",
        "culture": "Western",
        "communication_style": "formal, evidence-based, citations required",
        "values": "rigor, peer review, methodology",
        "concerns": ["methodology rigor", "statistical significance", "reproducibility", "source credibility"]
    },
    "business_uk": {
        "group": "business",
        "location": "United Kingdom",
        "culture": "Western",
        "communication_style": "professional, diplomatic, understated humor",
        "values": "efficiency, ROI, bottom line",
        "concerns": ["business case", "cost-benefit", "implementation timeline", "risk management"]
    },
    "business_asia": {
        "group": "business",
        "location": "Asia",
        "culture": "Eastern",
        "communication_style": "indirect, hierarchical respect, relationship-focused",
        "values": "harmony, long-term relationships, collective benefit",
        "concerns": ["team harmony", "stakeholder alignment", "cultural sensitivity", "long-term viability"]
    },
    "academic_europe": {
        "group": "academic",
        "location": "Europe",
        "culture": "Western",
        "communication_style": "philosophical, critical, detailed",
        "values": "depth, critique, contextualization",
        "concerns": ["historical context", "theoretical framework", "societal impact", "ethical dimensions"]
    },
    "community": {
        "group": "community",
        "location": "Diverse",
        "culture": "Multicultural",
        "communication_style": "accessible, practical, storytelling",
        "values": "relevance, real-world impact, inclusivity",
        "concerns": ["practical application", "community benefit", "accessibility", "cultural appropriateness"]
    },
    "startup": {
        "group": "business",
        "location": "Global",
        "culture": "Innovation-focused",
        "communication_style": "fast-paced, iterative, direct",
        "values": "speed, innovation, disruption potential",
        "concerns": ["market fit", "scalability", "competitive advantage", "growth potential"]
    }
}

FEEDBACK_PROMPT = '''You are providing feedback as a representative of a specific audience segment.

**Audience Profile:**
- Group Type: {group}
- Location/Region: {location}
- Culture: {culture}
- Communication Style: {communication_style}
- Core Values: {values}
- Key Concerns: {concerns}

**Content Assessment:**
Presenter said: "{text}"

Evaluate this presentation from your perspective and provide structured feedback. Consider:
1. How well does it align with your group's values and concerns?
2. What critical questions would you ask?
3. What cultural or contextual adjustments would improve it?
4. Rate the relevance to your group (1-10)
5. What specific action or next step do you recommend?

Return ONLY valid JSON (no markdown, no extra text):
{{
  "feedback_type": "constructive|critical|supportive|skeptical",
  "relevance_score": <1-10>,
  "key_concern": "most important point to address",
  "critical_question": "what would you ask the presenter?",
  "cultural_note": "any cultural or contextual adjustment needed, or null",
  "recommendation": "specific actionable feedback",
  "alignment_with_values": "how well does it align with core values?"
}}'''


async def simulate_feedback(
    text: str,
    feedback_setting: str = "academic_us",
    complexity: str = "medium",
    environment: str = "professional",
) -> dict:
    """
    Simulate feedback from a specific audience segment based on settings.
    
    Args:
        text: The content to get feedback on
        feedback_setting: Key from FEEDBACK_SETTINGS (e.g., "academic_us", "business_asia")
        complexity: "low", "medium", "high"
        environment: "professional", "academic", "community"
    
    Returns:
        Structured feedback response
    """
    settings = FEEDBACK_SETTINGS.get(feedback_setting, FEEDBACK_SETTINGS["academic_us"])
    
    concerns_str = ", ".join(settings["concerns"])
    prompt = FEEDBACK_PROMPT.format(
        group=settings["group"],
        location=settings["location"],
        culture=settings["culture"],
        communication_style=settings["communication_style"],
        values=settings["values"],
        concerns=concerns_str,
        text=text[:300],
    )
    
    try:
        client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.6,
        )
        raw = response.choices[0].message.content.strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        payload = json.loads(clean)
    except Exception as e:
        payload = {
            "feedback_type": "supportive",
            "relevance_score": 5,
            "key_concern": "Unable to process feedback",
            "critical_question": "Could you provide more context?",
            "cultural_note": None,
            "recommendation": "Please continue with your presentation",
            "alignment_with_values": "Neutral"
        }
    
    payload["setting"] = feedback_setting
    payload["group"] = settings["group"]
    payload["location"] = settings["location"]
    payload["culture"] = settings["culture"]
    return {"agent": "feedback", "type": "feedback", "payload": payload}


def get_available_feedback_settings() -> dict:
    """Return all available feedback settings for configuration."""
    return {
        key: {
            "group": settings["group"],
            "location": settings["location"],
            "culture": settings["culture"],
        }
        for key, settings in FEEDBACK_SETTINGS.items()
    }
