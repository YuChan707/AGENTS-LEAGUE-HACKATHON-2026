import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.feedback import simulate_feedback, get_available_feedback_settings

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    text: str
    feedback_setting: str = "academic_us"
    complexity: str = "medium"
    environment: str = "professional"


@router.get("/feedback/settings")
async def get_feedback_settings():
    """
    Get available feedback settings (locations, cultures, group types).
    
    Returns:
        dict: Available feedback settings with their configurations
    """
    return get_available_feedback_settings()


@router.post("/feedback/generate")
async def generate_feedback(request: FeedbackRequest):
    """
    Generate feedback for content based on specified audience settings.
    
    Args:
        request: FeedbackRequest with text, feedback_setting, complexity, environment
    
    Returns:
        dict: Structured feedback response from the selected audience
    """
    if not request.text or len(request.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Text must be at least 5 characters")
    
    feedback_response = await simulate_feedback(
        text=request.text,
        feedback_setting=request.feedback_setting,
        complexity=request.complexity,
        environment=request.environment,
    )
    
    return feedback_response


@router.get("/feedback/available-perspectives")
async def get_available_perspectives():
    """
    Get list of all available feedback perspectives/settings.
    
    Returns:
        dict: Organized feedback perspectives by category
    """
    settings = get_available_feedback_settings()
    
    # Organize by group and location
    organized = {
        "academic": {},
        "business": {},
        "community": {}
    }
    
    for key, config in settings.items():
        group = config["group"]
        if group in organized:
            organized[group][key] = {
                "label": f"{config['location']} - {config['culture']}",
                "location": config["location"],
                "culture": config["culture"],
                "key": key
            }
    
    return organized
