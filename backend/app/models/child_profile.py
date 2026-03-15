from pydantic import BaseModel, Field
from typing import Optional


class Sensitivities(BaseModel):
    violence: int = Field(3, ge=1, le=5)
    blood_gore: int = Field(3, ge=1, le=5)
    self_harm: int = Field(3, ge=1, le=5)
    suicide: int = Field(3, ge=1, le=5)
    gun_weapon: int = Field(3, ge=1, le=5)
    abuse: int = Field(3, ge=1, le=5)
    death_grief: int = Field(3, ge=1, le=5)
    sexual_content: int = Field(3, ge=1, le=5)
    bullying: int = Field(3, ge=1, le=5)
    substance_use: int = Field(3, ge=1, le=5)
    flash_seizure: int = Field(3, ge=1, le=5)
    loud_sensory: int = Field(3, ge=1, le=5)


class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age_band: str = Field(..., min_length=1, max_length=20)
    sensitivities: Sensitivities
    calming_strategy: str = Field("", max_length=500)


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age_band: Optional[str] = Field(None, min_length=1, max_length=20)
    sensitivities: Optional[Sensitivities] = None
    calming_strategy: Optional[str] = Field(None, max_length=500)


class ProfileResponse(BaseModel):
    id: str
    name: str
    age_band: str
    sensitivities: Sensitivities
    calming_strategy: str
    created_at: str
    updated_at: str
