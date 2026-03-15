"""
routers/viewing_plan.py
-----------------------
New router for viewing plan generation.
Does NOT modify or replace teammate's analysis router.
Reads segments already saved to Supabase by the analysis service.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import supabase
from app.services.viewing_plan import generate_plan_with_narration

router = APIRouter(prefix="/api/viewing-plan", tags=["viewing-plan"])


class ViewingPlanRequest(BaseModel):
    # child sensitivity sliders — 1=very sensitive, 5=not sensitive
    # keys match SENSITIVITY_FIELDS in CreateProfile.jsx exactly
    sensitivities    : dict
    child_name       : Optional[str] = "your child"
    calming_strategy : Optional[str] = "Take a short break and breathe."
    # optional per-flag action preferences
    # e.g. {"violence": "skip", "blood_gore": "blur", "flash_seizure": "skip"}
    handling_prefs   : Optional[dict] = {}


@router.post("/{movie_id}")
async def get_viewing_plan(movie_id: str, request: ViewingPlanRequest):
    """
    Generate a personalised viewing plan for a child profile.

    Requires the movie to have been analyzed first via:
    POST /api/analysis/{movie_id}

    Returns:
    - safe_segments: scenes with no threshold breaches
    - flagged_segments: scenes with action (skip/blur/warn/pause)
      and calming tip
    - overall_safety: safe / caution / not_recommended
    - parent_summary: plain language paragraph for the parent
    """

    # fetch movie with analyzed segments from Supabase
    result = supabase.table("movies").select("*").eq("id", movie_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie    = result.data[0]
    segments = movie.get("segments")

    if not segments:
        raise HTTPException(
            status_code=400,
            detail=(
                f"'{movie['title']}' has not been analyzed yet. "
                f"Call POST /api/analysis/{movie_id} first."
            )
        )

    profile = {
        "child_name"      : request.child_name,
        "sensitivities"   : request.sensitivities,
        "calming_strategy": request.calming_strategy,
        "handling_prefs"  : request.handling_prefs or {},
    }

    plan = await generate_plan_with_narration(
        movie_title = movie["title"],
        segments    = segments,
        profile     = profile,
    )

    return {
        "movie_id"      : movie_id,
        "movie_title"   : movie["title"],
        "movie_year"    : movie.get("year"),
        **plan
    }