from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from typing import List

from app.database import supabase
from app.models.child_profile import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def row_to_response(row: dict) -> ProfileResponse:
    return ProfileResponse(
        id=str(row["id"]),
        name=row.get("name", "Unknown"),
        age_band=row.get("age_band", "unknown"),
        sensitivities=row.get("sensitivities", {}),
        calming_strategy=row.get("calming_strategy", ""),
        created_at=str(row.get("created_at", "")),
        updated_at=str(row.get("updated_at", "")),
    )


@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(profile: ProfileCreate):
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "name": profile.name,
        "age_band": profile.age_band,
        "sensitivities": profile.sensitivities.model_dump(),
        "calming_strategy": profile.calming_strategy,
        "created_at": now,
        "updated_at": now,
    }
    result = supabase.table("profiles").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create profile")
    return row_to_response(result.data[0])


@router.get("", response_model=List[ProfileResponse])
async def list_profiles():
    result = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
    return [row_to_response(row) for row in result.data]


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str):
    result = supabase.table("profiles").select("*").eq("id", profile_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return row_to_response(result.data[0])


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: str, update: ProfileUpdate):
    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "sensitivities" in update_data and update_data["sensitivities"] is not None:
        update_data["sensitivities"] = (
            update_data["sensitivities"]
            if isinstance(update_data["sensitivities"], dict)
            else update.sensitivities.model_dump()
        )

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = supabase.table("profiles").update(update_data).eq("id", profile_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return row_to_response(result.data[0])


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    result = supabase.table("profiles").delete().eq("id", profile_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"deleted": True}
