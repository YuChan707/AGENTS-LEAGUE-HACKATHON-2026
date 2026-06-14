import os
import httpx

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Llama 4 Scout is Groq's multimodal model that accepts base64 images
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


async def analyze_frame(
    image_base64: str,
    persona: str,
    focus_area: str,
    environment: str,
    complexity: str,
) -> dict:
    """Send a JPEG screen-capture frame to Groq vision and return a visual coaching event."""

    prompt = (
        f"You are an AI presentation coach watching a live screen share.\n"
        f"Audience persona: {persona} | Focus area: {focus_area} | "
        f"Environment: {environment} | Complexity: {complexity}\n\n"
        "Look at this screenshot and respond with exactly two sentences:\n"
        "1. What slide or content is currently visible.\n"
        "2. One specific, actionable coaching tip for the presenter right now.\n"
        "Be concise and direct."
    )

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 120,
                "temperature": 0.5,
            },
        )
        response.raise_for_status()
        content: str = response.json()["choices"][0]["message"]["content"].strip()

    # Split into insight (full text) and tip (second sentence if present)
    sentences = [s.strip() for s in content.split(".") if s.strip()]
    tip = sentences[-1] if sentences else content

    return {
        "agent": "visual",
        "type": "visual",
        "payload": {
            "insight": content,
            "tip": tip,
        },
    }
