from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.services.analysis import analyze_movie

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/{movie_id}")
async def trigger_analysis(movie_id: str):
    """Trigger LLM content analysis for a single movie."""
    try:
        result = await analyze_movie(movie_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/batch/all")
async def trigger_batch_analysis():
    """Trigger LLM content analysis for all movies that haven't been analyzed yet."""
    movies = (
        supabase.table("movies")
        .select("id, title, analyzed_at, transcript_content")
        .is_("analyzed_at", "null")
        .order("title")
        .execute()
    )

    if not movies.data:
        return {"message": "All movies already analyzed", "analyzed": 0}

    # Filter to only movies with transcripts
    to_analyze = [m for m in movies.data if m.get("transcript_content")]
    results = []

    for movie in to_analyze:
        try:
            result = await analyze_movie(movie["id"])
            results.append({"id": movie["id"], "title": movie["title"], "status": "success"})
        except Exception as e:
            results.append({"id": movie["id"], "title": movie["title"], "status": "error", "error": str(e)})

    return {
        "analyzed": len([r for r in results if r["status"] == "success"]),
        "errors": len([r for r in results if r["status"] == "error"]),
        "results": results,
    }
