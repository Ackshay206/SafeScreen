"""
routers/recommendations.py
---------------------------
POST /api/recommendations
Accepts child profile form data, returns 3 safe movie recommendations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.recommender import get_recommendations

router = APIRouter(prefix="/api", tags=["recommendations"])


class ChildProfile(BaseModel):
    # Basic info
    child_name : Optional[str] = None
    age_band   : Optional[str] = None   # "4-6 yrs", "7-9 yrs" etc

    # Sensitivity sliders — 1=very sensitive, 5=not sensitive
    violence       : Optional[int] = 3
    blood          : Optional[int] = 3
    self_harm      : Optional[int] = 3
    suicide        : Optional[int] = 3
    gun_weapon     : Optional[int] = 3
    abuse          : Optional[int] = 3
    death_grief    : Optional[int] = 3
    sexual_content : Optional[int] = 3
    bullying       : Optional[int] = 3
    substance_use  : Optional[int] = 3
    flash_seizure  : Optional[int] = 3
    loud_sensory   : Optional[int] = 3

    # Optional calming strategy (stored but not used in filter)
    calming_strategy: Optional[str] = None

    # Optional reference movie (the movie they are about to watch)
    reference_title : Optional[str] = None
    reference_year  : Optional[int] = None


class RecommendationResponse(BaseModel):
    recommendations  : list = []
    candidates_count : int = 0
    reference_film   : Optional[str] = None
    mode             : str = "unknown"


@router.post("/recommendations", response_model=RecommendationResponse)
async def recommend_movies(profile: ChildProfile):
    """
    Takes a child profile and returns 3 safe movie recommendations.
    All sensitivity constraints are enforced before any LLM call.
    """

    # extract sensitivity sliders into dict
    sensitivity = {
        "violence"       : profile.violence,
        "blood"          : profile.blood,
        "self_harm"      : profile.self_harm,
        "suicide"        : profile.suicide,
        "gun_weapon"     : profile.gun_weapon,
        "abuse"          : profile.abuse,
        "death_grief"    : profile.death_grief,
        "sexual_content" : profile.sexual_content,
        "bullying"       : profile.bullying,
        "substance_use"  : profile.substance_use,
        "flash_seizure"  : profile.flash_seizure,
        "loud_sensory"   : profile.loud_sensory,
    }

    result = get_recommendations(
        profile          = sensitivity,
        age_band         = profile.age_band,
        reference_title  = profile.reference_title,
        reference_year   = profile.reference_year,
    )

    if "error" in result and not result["recommendations"]:
        raise HTTPException(status_code=404, detail=result["error"])

    return {
        "recommendations"  : result["recommendations"],
        "candidates_count" : result.get("candidates_count", 0),
        "reference_film"   : result.get("reference_film"),
        "mode"             : result.get("mode", "unknown")
    }
