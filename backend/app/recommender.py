"""
recommender.py
--------------
Groq (Llama 3.3 70B) recommendation engine.

Uses the 10 movies already in Supabase with their analyzed
overall_flags (produced by teammate's analysis service).
No Kaggle, no CSV, no pandas — pure Supabase + Groq.

Flow:
  1. Fetch all analyzed movies from Supabase
  2. Hard constraint filter — eliminate any movie that breaches
     the child's sensitivity thresholds on ANY dimension
  3. Exclude the reference movie the child is about to watch
  4. Call Groq to rank remaining safe movies by suitability
  5. Validate returned titles are in the safe pool
  6. Return top 3
"""

import os
import json

try:
    from groq import Groq
    groq_available = True
except ImportError:
    groq_available = False
    print("WARNING: groq not installed. Run: pip install groq")

from app.database import supabase

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"

if groq_available and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("Groq client initialised.")
else:
    groq_client = None
    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY not set. Using fallback mode.")


# ── sensitivity mapping ──
SEVERITY_TO_SCORE  = {"none": 0, "mild": 2, "moderate": 3, "intense": 5}
SLIDER_TO_MAX_SCORE = {1: 0, 2: 1, 3: 2, 4: 3, 5: 5}

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


def _fetch_analyzed_movies() -> list[dict]:
    result = (
        supabase.table("movies")
        .select("id, title, year, genre, mpaa_rating, synopsis, overall_flags")
        .not_.is_("overall_flags", "null")
        .execute()
    )
    return result.data or []


def _fetch_all_movies() -> list[dict]:
    result = (
        supabase.table("movies")
        .select("id, title, year, genre, mpaa_rating, synopsis, overall_flags")
        .execute()
    )
    return result.data or []


def _movie_passes_filter(movie: dict, sensitivity: dict) -> tuple[bool, list[str]]:
    overall_flags = movie.get("overall_flags") or {}
    failed = []

    for slider_key, user_rating in sensitivity.items():
        if user_rating is None:
            continue
        flag_key = SLIDER_TO_FLAG.get(slider_key)
        if not flag_key:
            continue
        severity_str = overall_flags.get(flag_key, "none")
        movie_score  = SEVERITY_TO_SCORE.get(severity_str, 0)
        max_allowed  = SLIDER_TO_MAX_SCORE.get(int(user_rating), 2)
        if movie_score > max_allowed:
            failed.append(flag_key)

    return (len(failed) == 0, failed)


SYSTEM_PROMPT = """
You are a child-safe movie recommendation specialist.
You receive a child sensitivity profile and a pre-filtered list
of candidate movies — ALL already verified safe for this child.

Rank the top 3 by suitability. Consider age-appropriateness,
tone, and similarity to the reference movie if provided.

RULES:
- Only recommend movies from the candidate list — never invent titles
- Do not recommend the reference movie itself
- Do not add sensitivity warnings — all movies are already safe

Return ONLY valid JSON, no markdown:
{
  "recommendations": [
    {
      "rank": 1,
      "title": "<exact title from candidate list>",
      "year": <year>,
      "genres": "<genres>",
      "similarity_score": <0.0-1.0>,
      "reason": "<one sentence why this suits this child>"
    }
  ]
}
"""


def _build_groq_prompt(sensitivity, candidates, reference_title=None, age_band=None):
    profile_lines = "\n".join([
        f"  {k.replace('_', ' ').title()}: {v}/5"
        for k, v in sensitivity.items() if v is not None
    ])
    ref_str = (
        f"Reference movie (about to watch): {reference_title}"
        if reference_title else "No reference movie."
    )
    age_str = f"Child age band: {age_band}" if age_band else ""
    candidate_lines = []
    for m in candidates:
        flags = m.get("overall_flags") or {}
        flag_summary = ", ".join([f"{k}:{v}" for k, v in flags.items() if v != "none"]) or "clean"
        candidate_lines.append(
            f"- {m['title']} ({m.get('year','?')}) | "f"Genres: {m.get('genre','?')} | Rated: {m.get('mpaa_rating','?')} | Flags: {flag_summary}"
        )
    return (
        f"Child profile (1=very sensitive, 5=not sensitive):\n{profile_lines}\n\n"
        f"{age_str}\n{ref_str}\n\n"
        f"Safe candidates ({len(candidates)} movies, all constraint-verified):\n"
        + "\n".join(candidate_lines)
        + "\n\nPick top 3. Return JSON only."
    )


def _fallback_recommendations(candidates, n=3):
    seen = set()
    unique = []
    for m in candidates:
        key = m["title"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(m)
    return [
        {
            "rank": i + 1,
            "title": m["title"],
            "year": m.get("year"),
            "genres": m.get("genre", ""),
            "similarity_score": 0.5,
            "reason": "Suitable for this sensitivity profile."
        }
        for i, m in enumerate(unique[:n])
    ]


def get_recommendations(profile, age_band=None, reference_title=None, reference_year=None):
    # fetch from Supabase
    movies = _fetch_analyzed_movies() or _fetch_all_movies()

    if not movies:
        return {"error": "No movies found in database.", "recommendations": [], "mode": "no_movies"}

    # hard constraint filter
    eligible   = []
    eliminated = []

    for movie in movies:
        if reference_title and movie["title"].lower() == reference_title.lower():
            continue
        passes, failed = _movie_passes_filter(movie, profile)
        if passes:
            eligible.append(movie)
        else:
            eliminated.append({"title": movie["title"], "failed": failed})

    print(f"Filter: {len(eligible)} eligible, {len(eliminated)} eliminated")

    if not eligible:
        return {
            "error": "No movies passed the constraint filter for this profile.",
            "recommendations": [], "mode": "no_results", "eliminated": eliminated
        }

    # Groq ranking
    if groq_client is None:
        return {
            "recommendations": _fallback_recommendations(eligible),
            "candidates_count": len(eligible),
            "reference_film": reference_title,
            "mode": "fallback_no_groq"
        }

    try:
        prompt   = _build_groq_prompt(profile, eligible, reference_title, age_band)
        response = groq_client.chat.completions.create(
            model           = GROQ_MODEL,
            messages        = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            temperature     = 0.2,
            max_tokens      = 1000,
            response_format = {"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content.strip())
        recs   = result.get("recommendations", [])

        valid_titles = {m["title"].lower() for m in eligible}
        recs = [r for r in recs if r.get("title", "").lower() in valid_titles]

        # Deduplicate by title
        seen = set()
        deduped = []
        for r in recs:
            key = r.get("title", "").lower()
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        recs = deduped

        # Only pad if we truly have more unique eligible movies
        if len(recs) < 3:
            already = {r["title"].lower() for r in recs}
            extras = [m for m in eligible if m["title"].lower() not in already]
            recs.extend(_fallback_recommendations(extras, n=3 - len(recs)))

        return {
            "recommendations": recs[:3],
            "candidates_count": len(eligible),
            "reference_film": reference_title,
            "mode": "groq_llama3"
        }

    except Exception as e:
        print(f"Groq error: {e}")
        return {
            "recommendations": _fallback_recommendations(eligible),
            "candidates_count": len(eligible),
            "reference_film": reference_title,
            "mode": "fallback_groq_error"
        }