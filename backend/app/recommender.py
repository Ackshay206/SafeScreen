"""
recommender.py
--------------
Purely deterministic recommendation engine.

Filters out movies based on user profile sensitivities.
If a user's sensitivity for a category is > 3 (Sensitive or Very Sensitive),
and the movie contains that flag, it is eliminated.
Returns the remaining safe movies without using any LLM.
"""

from app.database import supabase

# Maps frontend sensitivity keys to backend database flags
SLIDER_TO_FLAG = {
    "violence"      : "violence",
    "blood"         : "blood_gore",
    "self_harm"     : "self_harm",
    "suicide"       : "suicide",
    "gun_weapon"    : "gun_weapon",
    "abuse"         : "abuse",
    "death_grief"   : "death_grief",
    "sexual_content": "sexual_content",
    "bullying"      : "bullying",
    "substance_use" : "substance_use",
    "flash_seizure" : "flash_seizure",
    "loud_sensory"  : "loud_sensory",
}


def _fetch_all_movies() -> list[dict]:
    result = (
        supabase.table("movies")
        .select("id, title, year, genre, mpaa_rating, synopsis, overall_flags, poster_url")
        .execute()
    )
    return result.data or []


def get_recommendations(profile, age_band=None, reference_title=None, reference_year=None):
    movies = _fetch_all_movies()

    if not movies:
        return {"error": "No movies found in database.", "recommendations": [], "mode": "no_movies"}

    eligible = []
    eliminated = []

    # Map user sensitivities > 3 to a list of strict flags they want to avoid
    strict_flags = []
    for slider_key, user_rating in profile.items():
        if user_rating is not None and user_rating > 3:
            flag_key = SLIDER_TO_FLAG.get(slider_key)
            if flag_key:
                strict_flags.append(flag_key)

    for movie in movies:
        # Exclude the reference movie if provided
        if reference_title and movie["title"].lower() == reference_title.lower():
            continue

        failed = []
        # overall_flags is now a list of strings (e.g., ["violence", "blood_gore"])
        movie_flags = movie.get("overall_flags") or []
        
        # Ensure it's treated as a list even if it was stored as a dict previously
        if isinstance(movie_flags, dict):
            movie_flags = [k for k, v in movie_flags.items() if v != 'none']

        for required_avoid in strict_flags:
            if required_avoid in movie_flags:
                failed.append(required_avoid)

        # Basic age rating constraint for R-rated movies
        is_adult = False
        try:
            if age_band and (str(age_band).lower() in ["18+", "adult"] or int(age_band) >= 18):
                is_adult = True
        except:
            pass

        rating = (movie.get("mpaa_rating") or "").upper()
        if not is_adult and rating == "R":
            failed.append("AGE_RESTRICTED_R")

        if len(failed) == 0:
            eligible.append(movie)
        else:
            eliminated.append({"title": movie["title"], "failed": failed})

    print(f"Filter: {len(eligible)} eligible, {len(eliminated)} eliminated")

    if not eligible:
        return {
            "error": "No completely safe movies found for this profile.",
            "recommendations": [], 
            "mode": "no_results"
        }

    # Format the response list
    recommendations = []
    for i, m in enumerate(eligible):
        recommendations.append({
            "rank": i + 1,
            "title": m["title"],
            "year": m.get("year"),
            "genres": m.get("genre", ""),
            "similarity_score": 1.0,  # Pure deterministic match
            "reason": f"Safe viewing choice. No triggers matched regarding {', '.join([k.replace('_', ' ') for k in strict_flags])}." if strict_flags else "Perfectly safe based on your profile constraints."
        })

    return {
        "recommendations": recommendations,
        "candidates_count": len(eligible),
        "reference_film": reference_title,
        "mode": "deterministic_filter"
    }