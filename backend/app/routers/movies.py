from fastapi import APIRouter, HTTPException
from typing import List

from app.database import supabase
from app.models.movie import MovieListItem, MovieDetail, MovieSafetySummary

router = APIRouter(prefix="/api/movies", tags=["movies"])


def row_to_list_item(row: dict) -> MovieListItem:
    return MovieListItem(
        id=row["id"],
        title=row["title"],
        year=row["year"],
        genre=row.get("genre", []),
        poster_url=row.get("poster_url", ""),
        mpaa_rating=row.get("mpaa_rating", "NR"),
        overall_flags=row.get("overall_flags", {}),
    )


def row_to_detail(row: dict) -> MovieDetail:
    return MovieDetail(
        id=row["id"],
        title=row["title"],
        year=row["year"],
        genre=row.get("genre", []),
        runtime_minutes=row.get("runtime_minutes", 0),
        poster_url=row.get("poster_url", ""),
        synopsis=row.get("synopsis", ""),
        mpaa_rating=row.get("mpaa_rating", "NR"),
        overall_flags=row.get("overall_flags", {}),
        segments=row.get("segments", []),
        plain_language_summary=row.get("plain_language_summary", ""),
        analyzed_at=row.get("analyzed_at"),
    )


@router.get("", response_model=List[MovieListItem])
async def list_movies():
    result = (
        supabase.table("movies")
        .select("id, title, year, genre, poster_url, mpaa_rating, overall_flags")
        .order("title")
        .execute()
    )
    return [row_to_list_item(row) for row in result.data]


@router.get("/{movie_id}", response_model=MovieDetail)
async def get_movie(movie_id: str):
    result = supabase.table("movies").select("*").eq("id", movie_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Movie not found")
    return row_to_detail(result.data[0])


@router.get("/{movie_id}/safety", response_model=MovieSafetySummary)
async def get_movie_safety(movie_id: str):
    result = (
        supabase.table("movies")
        .select("id, title, overall_flags, plain_language_summary")
        .eq("id", movie_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Movie not found")
    row = result.data[0]
    return MovieSafetySummary(
        id=row["id"],
        title=row["title"],
        overall_flags=row.get("overall_flags", {}),
        plain_language_summary=row.get("plain_language_summary", ""),
    )
