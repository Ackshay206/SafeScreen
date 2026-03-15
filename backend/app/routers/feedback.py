"""
routers/feedback.py
-------------------
Handles post-watch feedback submission.
Stores feedback in Supabase and generates personalised
calming YouTube video suggestions.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.database import supabase
from app.services.feedback import generate_calming_videos

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    profile_id: str
    movie_id: str
    plan_id: Optional[str] = None
    strictness_rating: str  # "too_strict" | "about_right" | "too_loose"
    child_seemed_distressed: bool = False
    distress_level: str = "none"  # "none" | "mild" | "moderate" | "severe"
    triggered_flags: list[str] = []
    optional_note: str = ""


class FeedbackResponse(BaseModel):
    feedback_id: Optional[str] = None
    message: str
    calming_videos: list[dict] = []
    show_calming: bool = False


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit post-watch feedback and receive personalised
    calming video suggestions if the viewer was distressed.
    """

    # 1. Fetch profile for calming strategy
    profile_result = supabase.table("profiles").select("*").eq("id", request.profile_id).execute()
    if not profile_result.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = profile_result.data[0]

    # 2. Fetch movie title
    movie_result = supabase.table("movies").select("title").eq("id", request.movie_id).execute()
    movie_title = movie_result.data[0]["title"] if movie_result.data else "Unknown Movie"

    # 3. Find plan_id if not provided
    plan_id = request.plan_id
    if not plan_id:
        plan_result = (
            supabase.table("viewing_plans")
            .select("id")
            .eq("profile_id", request.profile_id)
            .eq("movie_id", request.movie_id)
            .execute()
        )
        if plan_result.data:
            plan_id = plan_result.data[0]["id"]

    # 4. Store feedback
    feedback_row = {
        "profile_id": request.profile_id,
        "movie_id": request.movie_id,
        "plan_id": plan_id,
        "strictness_rating": request.strictness_rating,
        "child_seemed_distressed": request.child_seemed_distressed,
        "optional_note": request.optional_note or "",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    feedback_id = None
    try:
        insert_result = supabase.table("feedback").insert(feedback_row).execute()
        if insert_result.data:
            feedback_id = insert_result.data[0]["id"]
    except Exception as e:
        print(f"Warning: Failed to store feedback: {e}")

    # 5. Generate calming videos if distressed
    calming_videos = []
    show_calming = request.child_seemed_distressed or request.distress_level in ("moderate", "severe")

    if show_calming:
        calming_videos = await generate_calming_videos(
            viewer_name=profile.get("name", "the viewer"),
            age=profile.get("age"),
            calming_strategy=profile.get("calming_strategy", "Take a deep breath"),
            triggered_content=request.triggered_flags,
            feedback_note=request.optional_note,
            distress_level=request.distress_level,
        )

    # 6. Build response message
    if show_calming:
        message = f"Thank you for your feedback. We've prepared some calming videos for {profile.get('name', 'you')} based on their preferences."
    elif request.strictness_rating == "too_strict":
        message = "Thanks! We'll use this feedback to fine-tune future viewing plans."
    elif request.strictness_rating == "too_loose":
        message = "Thanks for letting us know. We'll make future plans more cautious."
    else:
        message = "Great to hear the plan worked well! Your feedback helps us improve."

    return FeedbackResponse(
        feedback_id=feedback_id,
        message=message,
        calming_videos=calming_videos,
        show_calming=show_calming,
    )


@router.get("/{movie_id}/{profile_id}")
async def get_existing_feedback(movie_id: str, profile_id: str):
    """Check if feedback already exists for this movie+profile."""
    result = (
        supabase.table("feedback")
        .select("*")
        .eq("movie_id", movie_id)
        .eq("profile_id", profile_id)
        .execute()
    )

    if not result.data:
        return {"exists": False}

    return {"exists": True, "feedback": result.data[0]}