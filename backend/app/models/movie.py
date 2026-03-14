from pydantic import BaseModel, Field
from typing import List, Optional


class SegmentFlags(BaseModel):
    violence: int = Field(0, ge=0, le=5)
    blood_gore: int = Field(0, ge=0, le=5)
    self_harm: int = Field(0, ge=0, le=5)
    suicide: int = Field(0, ge=0, le=5)
    gun_weapon: int = Field(0, ge=0, le=5)
    abuse: int = Field(0, ge=0, le=5)
    death_grief: int = Field(0, ge=0, le=5)
    sexual_content: int = Field(0, ge=0, le=5)
    bullying: int = Field(0, ge=0, le=5)
    substance_use: int = Field(0, ge=0, le=5)
    flash_seizure: int = Field(0, ge=0, le=5)
    loud_sensory: int = Field(0, ge=0, le=5)


class Segment(BaseModel):
    segment_id: int
    start_time: str
    end_time: str
    summary: str
    flags: SegmentFlags


class OverallFlags(BaseModel):
    violence: str = "none"
    blood_gore: str = "none"
    self_harm: str = "none"
    suicide: str = "none"
    gun_weapon: str = "none"
    abuse: str = "none"
    death_grief: str = "none"
    sexual_content: str = "none"
    bullying: str = "none"
    substance_use: str = "none"
    flash_seizure: str = "none"
    loud_sensory: str = "none"


class MovieListItem(BaseModel):
    id: str
    title: str
    year: int
    genre: List[str]
    poster_url: str
    mpaa_rating: str
    overall_flags: OverallFlags


class MovieDetail(BaseModel):
    id: str
    title: str
    year: int
    genre: List[str]
    runtime_minutes: int
    poster_url: str
    synopsis: str
    mpaa_rating: str
    overall_flags: OverallFlags
    segments: List[Segment]
    plain_language_summary: str
    analyzed_at: Optional[str] = None


class MovieSafetySummary(BaseModel):
    id: str
    title: str
    overall_flags: OverallFlags
    plain_language_summary: str
