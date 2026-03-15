"""
routers/viewing_plan.py
-----------------------
Router for viewing plan generation.
Accepts a profile_id, fetches the profile AND full movie data
from Supabase, passes everything to Gemini 2.5 Pro for
AI-powered viewing plan generation, and stores the result.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.database import supabase
from app.services.viewing_plan import generate_plan_with_narration

router = APIRouter(prefix="/api/viewing-plan", tags=["viewing-plan"])


class ViewingPlanRequest(BaseModel):
    profile_id: str


class ViewingPlanResponse(BaseModel):
    plan_id: Optional[str] = None
    movie_id: str
    movie_title: str
    movie_year: Optional[int] = None
    profile_id: str
    profile_name: str
    child_name: str
    child_age: Optional[int] = None
    calming_strategy: str
    total_segments: int
    safe_segments: int
    flagged_segments: int
    overall_mode: dict
    sessions: list
    segment_actions: list
    parent_summary: str


@router.post("/{movie_id}", response_model=ViewingPlanResponse)
async def get_viewing_plan(movie_id: str, request: ViewingPlanRequest):
    """
    Generate a personalised viewing plan for a profile using Gemini 2.5 Pro.

    Requires:
    - The movie to have been analyzed (POST /api/analysis/{movie_id})
    - A valid profile_id

    The full movie data (including synopsis, overall flags, and all segments)
    and the full profile data (including sensitivities, age, calming strategy,
    and additional context) are sent to Gemini for intelligent plan generation.
    """

    # 1. Fetch profile with ALL fields
    profile_result = supabase.table("profiles").select("*").eq("id", request.profile_id).execute()
    if not profile_result.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile_row = profile_result.data[0]

    # 2. Fetch FULL movie data (not just segments)
    movie_result = supabase.table("movies").select("*").eq("id", movie_id).execute()
    if not movie_result.data:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie = movie_result.data[0]
    segments = movie.get("segments")

    if not segments:
        raise HTTPException(
            status_code=400,
            detail=(
                f"'{movie['title']}' has not been analyzed yet. "
                f"Call POST /api/analysis/{movie_id} first."
            )
        )

    # 3. Build rich profile dict with ALL available context
    sensitivities = profile_row.get("sensitivities", {})
    child_name = profile_row.get("name", "your child")
    age = profile_row.get("age")
    calming_strategy = profile_row.get("calming_strategy", "Take a short break and breathe.")
    additional_details = profile_row.get("additional_details", "")

    profile = {
        "child_name": child_name,
        "age": age,
        "sensitivities": sensitivities,
        "calming_strategy": calming_strategy,
        "additional_details": additional_details,
    }

    # 4. Generate the AI-powered plan (passes full movie dict + segments + profile)
    plan = await generate_plan_with_narration(
        movie=movie,
        segments=segments,
        profile=profile,
    )

    # 5. Store the plan in viewing_plans table
    plan_row = {
        "profile_id": request.profile_id,
        "movie_id": movie_id,
        "sessions": plan.get("sessions", []),
        "total_sessions": len(plan.get("sessions", [])),
        "plan_summary": plan.get("parent_summary", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    plan_id = None
    try:
        # Check if a plan already exists for this profile+movie combo
        existing = (
            supabase.table("viewing_plans")
            .select("id")
            .eq("profile_id", request.profile_id)
            .eq("movie_id", movie_id)
            .execute()
        )

        if existing.data:
            # Update existing plan
            plan_id = existing.data[0]["id"]
            supabase.table("viewing_plans").update(plan_row).eq("id", plan_id).execute()
        else:
            # Insert new plan
            insert_result = supabase.table("viewing_plans").insert(plan_row).execute()
            if insert_result.data:
                plan_id = insert_result.data[0]["id"]
    except Exception as e:
        print(f"Warning: Failed to store viewing plan: {e}")

    return ViewingPlanResponse(
        plan_id=plan_id,
        movie_id=movie_id,
        movie_title=movie["title"],
        movie_year=movie.get("year"),
        profile_id=request.profile_id,
        profile_name=child_name,
        child_name=plan.get("child_name", child_name),
        child_age=plan.get("child_age", age),
        calming_strategy=plan.get("calming_strategy", calming_strategy),
        total_segments=plan.get("total_segments", 0),
        safe_segments=plan.get("safe_segments", 0),
        flagged_segments=plan.get("flagged_segments", 0),
        overall_mode=plan.get("overall_mode", {}),
        sessions=plan.get("sessions", []),
        segment_actions=plan.get("segment_actions", []),
        parent_summary=plan.get("parent_summary", ""),
    )


@router.get("/{movie_id}/{profile_id}")
async def get_existing_plan(movie_id: str, profile_id: str):
    """
    Fetch an existing viewing plan for a movie+profile combo.
    Returns 404 if no plan exists yet.
    """
    result = (
        supabase.table("viewing_plans")
        .select("*")
        .eq("movie_id", movie_id)
        .eq("profile_id", profile_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="No viewing plan found. Generate one first.")

    plan = result.data[0]
    return {
        "plan_id": plan["id"],
        "movie_id": plan["movie_id"],
        "profile_id": plan["profile_id"],
        "sessions": plan.get("sessions", []),
        "total_sessions": plan.get("total_sessions", 1),
        "plan_summary": plan.get("plan_summary", ""),
        "generated_at": plan.get("generated_at"),
    }