"""
Seed script: fetches movie metadata from OMDb and loads .srt transcripts.
Run with:  python -m app.seed

Place your .srt files in backend/transcripts/ named to match the MOVIES list below
(e.g. "The Dark Knight.srt", "Inside Out 2.srt").
"""
import os
import sys
import requests
from datetime import datetime, timezone
from app.database import supabase
from app.config import SUPABASE_URL

OMDB_API_KEY = "7ca1daa0"
OMDB_BASE = "http://www.omdbapi.com/"
TRANSCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "transcripts")

# ---- Movie list: OMDb search title → exact .srt filename ----
MOVIES = [
    {"title": "Alien", "year": "1979", "srt": "Alien (1979) Director's Cut.srt"},
    {"title": "Forrest Gump", "year": "1994", "srt": "Forrest Gump.srt"},
    {"title": "Halloween", "year": "1978", "srt": "Halloween (1978) UHD BluRay 2160p HDR10 DV HEVC TrueHD Atmos 7.1 x265-E.eng.srt"},
    {"title": "Inside Out", "year": "2015", "srt": "Inside Out.2015.UHDRip.2160u.HDR-DV.Eng-Songs.srt"},
    {"title": "Jaws 3-D", "year": "1983", "srt": "Jaws.3-D.1983.1080p.BluRay.x264.AAC-[YTS.MX].en.srt"},
    {"title": "Saw", "year": "2004", "srt": "SAW (2004) [1080p] 23.976FPS 1.43.10TIME.en.srt"},
    {"title": "The Godfather", "year": "1972", "srt": "The Godfather (1972).eng.sdh.srt"},
    {"title": "The Lion King", "year": "2019", "srt": "The.Lion.King.2019.1080p.BluRay.x265-YAWNTiC_eng.srt"},
    {"title": "Toy Story", "year": "1995", "srt": "Toy Story (1995) Bluray-1080p Proper.en.srt"},
    {"title": "Zootopia", "year": "2016", "srt": "Zootopia (2016) 1080P DSNP WEB-DL DDP5.1 Atmos H264 TURG_English.srt"},
]


def fetch_omdb(title: str, year: str = None) -> dict | None:
    """Fetch movie metadata from OMDb API."""
    params = {"t": title, "plot": "full", "apikey": OMDB_API_KEY}
    if year:
        params["y"] = year
    resp = requests.get(OMDB_BASE, params=params)
    data = resp.json()
    if data.get("Response") == "False":
        print(f"  ⚠️  OMDb lookup failed for '{title}': {data.get('Error')}")
        return None
    return data


def parse_runtime(runtime_str: str) -> int:
    """Parse '152 min' → 152."""
    try:
        return int(runtime_str.replace(" min", "").replace("N/A", "0"))
    except (ValueError, AttributeError):
        return 0


def load_transcript(srt_filename: str) -> str | None:
    """Load .srt transcript from the transcripts/ directory."""
    filepath = os.path.join(TRANSCRIPTS_DIR, srt_filename)
    if not os.path.exists(filepath):
        print(f"  ℹ️  No transcript found: {srt_filename}")
        return None
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def omdb_to_row(omdb_data: dict, transcript: str | None, srt_filename: str) -> dict:
    """Convert OMDb response to our movies table row."""
    genres = [g.strip() for g in omdb_data.get("Genre", "").split(",") if g.strip()]
    poster = omdb_data.get("Poster", "")
    if poster == "N/A":
        poster = ""

    return {
        "title": omdb_data.get("Title", ""),
        "year": int(omdb_data.get("Year", "0")[:4]),
        "genre": genres,
        "runtime_minutes": parse_runtime(omdb_data.get("Runtime", "0 min")),
        "poster_url": poster,
        "synopsis": omdb_data.get("Plot", ""),
        "mpaa_rating": omdb_data.get("Rated", "NR"),
        "transcript_file": srt_filename,
        "overall_flags": {},           # populated later by LLM analysis
        "segments": [],                # populated later by LLM analysis
        "plain_language_summary": "",   # populated later
        "analyzed_at": None,
        "transcript_content": transcript,
    }


def seed():
    # Clear existing movies
    print("Clearing existing movies...")
    supabase.table("movies").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    print(f"\nFetching metadata for {len(MOVIES)} movies from OMDb...\n")

    rows = []
    for movie in MOVIES:
        title, year, srt = movie["title"], movie["year"], movie["srt"]
        print(f"📥 {title} ({year})")
        omdb_data = fetch_omdb(title, year)
        if not omdb_data:
            continue

        transcript = load_transcript(srt)
        row = omdb_to_row(omdb_data, transcript, srt)
        rows.append(row)
        print(f"  ✅ {row['title']} ({row['year']}) — {row['mpaa_rating']} — {row['runtime_minutes']} min")
        if transcript:
            print(f"  📄 Transcript loaded ({len(transcript):,} chars)")

    if not rows:
        print("\n❌ No movies to insert.")
        return

    result = supabase.table("movies").insert(rows).execute()
    print(f"\n🎬 Inserted {len(result.data)} movies into Supabase.")
    for row in result.data:
        has_transcript = "📄" if row.get("transcript_content") else "—"
        print(f"  {row['title']}: {row['id']}  {has_transcript}")


if __name__ == "__main__":
    seed()
