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
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False
    print("WARNING: openai not installed. Run: pip install openai")

from app.database import supabase

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL   = "gpt-4o"

if openai_available and OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI client initialised.")
else:
    openai_client = None
    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY not set. Using fallback mode.")


# ── sensitivity mapping ──
# Intensity Scale in movies: none=0, mild=2, moderate=3, intense=5
SEVERITY_TO_SCORE  = {"none": 0, "mild": 2, "moderate": 3, "intense": 5}

# User Sensitivity Scale: 1 (Not Sensitive) ⮕ 5 (Very Sensitive)
# Intensity Scale in movies: none=0, mild=2, moderate=3, intense=5
# For a movie to be "Hard Blocked," it must be significantly over the limit.
# For adults, we allow more through to let the LLM decide.
SLIDER_TO_MAX_SCORE = {
    1: 5,  # Not sensitive: Allow up to Intense (5)
    2: 5,  # Low: Allow up to Intense (5)
    3: 5,  # Moderate: Allow up to Intense (5) for adults (LLM will deprioritize)
    4: 3,  # High: Only up to Moderate (3)
    5: 2,  # Very high: Only up to Mild (2)
}

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
        .select("id, title, year, genre, mpaa_rating, synopsis, overall_flags, segments")
        .not_.is_("overall_flags", "null")
        .execute()
    )
    return result.data or []


def _fetch_all_movies() -> list[dict]:
    result = (
        supabase.table("movies")
        .select("id, title, year, genre, mpaa_rating, synopsis, overall_flags, segments")
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
You are a highly capable movie recommendation specialist.
You receive a user profile (age, sensitivity levels) and a list of candidate movies.
Each movie includes its "Content Intensities" (None, Mild, Moderate, Intense).

### YOUR CORE MISSION:
Rank the top 3 recommendations. You must prioritize EXTREME safety for any trigger the user is "Sensitive" to (Sensitivity 4 or 5).

### RANKING RULES:
1. **Zero Tolerance for High Sensitivity**: If a user has Sensitivity 4 or 5 for a category (e.g., Bullying), you MUST prioritize movies that have "NONE" in that category over those with "MILD". Only recommend a "MILD" movie if no "NONE" options remain in the pool.
2. **Adult Relevance**: For users 18+, aim for high-quality, iconic cinema (like 'Alien', 'The Lion King', 'Zootopia') rather than just preschool content, provided they pass the safety check.
3. **Reasoning**: Your reason must explain how the movie respects their specific sensitive triggers.

Return ONLY valid JSON:
{
  "recommendations": [
    {
      "rank": 1,
      "title": "<exact title from candidate list>",
      "year": <year>,
      "genres": "<genres>",
      "similarity_score": <0.0-1.0>,
      "reason": "<Tailored explanation focusing on their HIGH SENSITIVITY triggers.>"
    }
  ]
}
"""


def _build_openai_prompt(sensitivity, candidates, reference_title=None, age_band=None):
    # Highlight high-sensitivity triggers for the LLM
    high_sens = [k.replace('_', ' ').title() for k, v in sensitivity.items() if v and int(v) >= 4]
    sens_warning = f"CRITICAL: User is highly sensitive to: {', '.join(high_sens)}" if high_sens else ""

    profile_lines = "\n".join([
        f"  {k.replace('_', ' ').title()}: {v}/5"
        for k, v in sensitivity.items() if v is not None
    ])
    ref_str = (
        f"Reference movie: {reference_title}"
        if reference_title else "No reference movie."
    )
    age_str = f"User age: {age_band}" if age_band else ""
    
    candidate_lines = []
    for m in candidates:
        flags = m.get("overall_flags") or {}
        flag_summary = ", ".join([f"{k.replace('_', ' ')}: {v.upper()}" for k, v in flags.items() if v != "none"]) or "CLEAN"
        synopsis = m.get("synopsis", "No synopsis.")[:150] + "..."
        candidate_lines.append(
            f"- {m['title']} ({m.get('year','?')}) | Rated: {m.get('mpaa_rating','?')} | Intensities: [{flag_summary}] | Synopsis: {synopsis}"
        )
        
    return (
        f"{sens_warning}\n"
        f"User Age: {age_str}\n"
        f"User Sensitivity Profile (1=Not Sensitive, 5=Very Sensitive):\n{profile_lines}\n\n"
        f"{ref_str}\n\n"
        f"Safe candidates ({len(candidates)} movies):\n"
        + "\n".join(candidate_lines)
        + "\n\nSelect top 3. JSON only."
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
            
        is_adult = False
        try:
            # Simple check for adult age bands or explicit age
            if age_band and (str(age_band).lower() in ["18+", "adult"] or int(age_band) >= 18):
                is_adult = True
        except:
            pass

        passes, failed = _movie_passes_filter(movie, profile)
        
        # 1. Hard Rating Block: Block R for under 18s
        rating = (movie.get("mpaa_rating") or "").upper()
        if not is_adult and rating == "R":
            eliminated.append({"title": movie["title"], "failed": ["AGE_RESTRICTED_R"]})
            continue

        # 2. Logic: If adult, we are much more permissive in the "Hard Filter" phase
        if passes or (is_adult and len(failed) <= 2):
            eligible.append(movie)
        else:
            eliminated.append({"title": movie["title"], "failed": failed})

    print(f"Filter: {len(eligible)} eligible, {len(eliminated)} eliminated")

    if not eligible:
        return {
            "error": "No movies passed the constraint filter for this profile.",
            "recommendations": [], "mode": "no_results", "eliminated": eliminated
        }

    # OpenAI ranking
    if openai_client is None:
        return {
            "recommendations": _fallback_recommendations(eligible),
            "candidates_count": len(eligible),
            "reference_film": reference_title,
            "mode": "fallback_no_openai"
        }

    try:
        prompt   = _build_openai_prompt(profile, eligible, reference_title, age_band)
        response = openai_client.chat.completions.create(
            model           = OPENAI_MODEL,
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
            "mode": "openai_gpt4o"
        }

    except Exception as e:
        print(f"OpenAI error: {e}")
        return {
            "recommendations": _fallback_recommendations(eligible),
            "candidates_count": len(eligible),
            "reference_film": reference_title,
            "mode": "fallback_openai_error"
        }