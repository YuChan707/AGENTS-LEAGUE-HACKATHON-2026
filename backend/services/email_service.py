from services.llm_factory import get_llm_client, get_model

FOCUS_DESC = {
    "marketing": "brand engagement and audience emotional response",
    "finance": "investor conviction and financial objection handling",
    "business": "executive decision readiness and strategic alignment",
}

PROMPT = """Professional executive assistant writing a follow-up email.
After a presentation practice session:
- Persona: {persona}
- Focus: {focus} ({focus_desc})
- Region: {region}
- Engagement: {engagement:.0%}
- Conviction: {conviction:.0%}
- Top group: {top_group}
- Key insight: {key_insight}

Structure exactly:
Subject: [subject line]

[2 sentences: what was observed]

[2 sentences: key insight and meaning]

[1 sentence: recommended next action]

Max 150 words. Professional tone. No markdown. No JSON."""


async def generate_email_draft(session_summary: dict) -> dict:
    analytics = session_summary.get("analytics", {})
    groups = session_summary.get("audience_groups", [])
    focus = session_summary.get("focus_area", "business")
    top_group = groups[0]["group_label"] if groups else "General Audience"
    key_insight = groups[0].get("behavioral_pattern", "mixed engagement") if groups else "varied response"

    prompt = PROMPT.format(
        persona=session_summary.get("persona_type", "executive").title(),
        focus=focus.title(),
        focus_desc=FOCUS_DESC.get(focus, "audience analysis"),
        region=session_summary.get("region", "us").upper(),
        engagement=analytics.get("engagement_level", 0.0),
        conviction=analytics.get("conviction_level", 0.0),
        top_group=top_group,
        key_insight=key_insight,
    )
    try:
        client = get_llm_client()
        response = await client.chat.completions.create(
            model=get_model(fast=False),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4,
        )
        raw = response.choices[0].message.content.strip()
    except Exception:
        raw = "Subject: Onlooker Session Follow-Up\n\nSession completed successfully.\n\nReview your scores in the dashboard.\n\nSchedule your next practice session."

    lines = [l for l in raw.split("\n") if l.strip()]
    subj_line = next((l for l in lines if l.lower().startswith("subject:")), "Subject: Session Follow-Up")
    subject = subj_line.replace("Subject:", "").replace("subject:", "").strip()
    body = "\n\n".join(l for l in lines if not l.lower().startswith("subject:"))
    return {"subject": subject, "body": body, "full_text": raw}
