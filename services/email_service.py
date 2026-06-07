
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from dotenv import load_dotenv

load_dotenv()

def _build_deep_kernel():
    """Use Llama 70B for richer email writing quality."""
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(
        service_id="groq_deep",
        ai_model_id="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    ))
    return kernel


EMAIL_PROMPT = """You are a professional executive assistant.
Write a follow-up email after a presentation practice session.

Session data:
- Persona analyzed: {persona_type}
- Focus area: {focus_area} ({focus_desc})
- Region: {region}
- Engagement score: {engagement:.0%}
- Conviction score: {conviction:.0%}
- Top audience group: {top_group}
- Key behavioral insight: {key_insight}
- Sessions objections raised: {objections}

Write exactly this structure:
Subject: [concise subject line]

[Paragraph 1 — 2 sentences: what the analysis observed]

[Paragraph 2 — 2 sentences: the key insight and what it means]

[Paragraph 3 — 1-2 sentences: one concrete recommended next action]

Max 150 words total. Professional tone. No markdown. No JSON. No bullet points."""


FOCUS_DESCRIPTIONS = {
    "marketing": "brand engagement and audience emotional response",
    "finance":   "investor conviction and financial objection handling",
    "business":  "executive decision readiness and strategic alignment"
}


async def generate_email_draft(session_summary: dict) -> dict:
    """
    Generate an Outlook-style follow-up email draft.
    Returns dict with subject and body separated for UI rendering.
    """
    kernel = _build_deep_kernel()

    analytics = session_summary.get("analytics", {})
    groups = session_summary.get("audience_groups", [])

    top_group = groups[0]["group_label"] if groups else "General Audience"
    key_insight = (
        groups[0].get("behavioral_pattern", "mixed engagement detected")
        if groups else "audience response was varied"
    )

    focus = session_summary.get("focus_area", "business")

    prompt = EMAIL_PROMPT.format(
        persona_type=session_summary.get("persona_type", "executive").title(),
        focus_area=focus.title(),
        focus_desc=FOCUS_DESCRIPTIONS.get(focus, "audience analysis"),
        region=session_summary.get("region", "us").upper(),
        engagement=analytics.get("engagement_level", 0.0),
        conviction=analytics.get("conviction_level", 0.0),
        top_group=top_group,
        key_insight=key_insight,
        objections=int(analytics.get("objection_count", 0))
    )

    result = await kernel.invoke_prompt(prompt)
    raw_text = str(result).strip()

    # Split subject from body for UI rendering
    lines = [l for l in raw_text.split("\n") if l.strip()]
    subject_line = next(
        (l for l in lines if l.lower().startswith("subject:")),
        "Subject: Onlooker Session Follow-Up"
    )
    subject = subject_line.replace("Subject:", "").replace("subject:", "").strip()
    body = "\n\n".join(
        l for l in lines
        if not l.lower().startswith("subject:")
    )

    return {
        "subject": subject,
        "body": body,
        "full_text": raw_text,
        "persona": session_summary.get("persona_type"),
        "focus_area": focus
    }