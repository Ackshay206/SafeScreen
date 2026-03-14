"""
Content analysis service — uses GPT to analyze transcripts
and identify real scene boundaries with exact timestamps,
generate safety flags per scene, and create plain-language summaries.
"""
import json
from datetime import datetime, timezone
from openai import OpenAI

from app.config import OPENAI_API_KEY
from app.database import supabase
from app.services.srt_parser import parse_srt, chunk_transcript

client = OpenAI(api_key=OPENAI_API_KEY)

CONTENT_FLAGS = [
    "violence", "blood_gore", "self_harm", "suicide", "gun_weapon", "abuse",
    "death_grief", "sexual_content", "bullying", "substance_use",
    "flash_seizure", "loud_sensory",
]

SCENE_DETECTION_PROMPT = """You are a media-safety content analyst. You are given a portion of a movie's subtitle transcript with timestamps. 

Identify the distinct SCENES in this transcript portion. For each scene, provide:
1. The EXACT start timestamp (HH:MM:SS) from the subtitle entries
2. The EXACT end timestamp (HH:MM:SS) from the subtitle entries
3. A 1-2 sentence summary of what happens
4. Content flag ratings (0-5 scale):
   0 = not present, 1 = barely implied, 2 = mildly present, 3 = moderate, 4 = strong, 5 = extremely intense/graphic

A "scene" is a distinct narrative unit — a change in location, action, mood, or topic. Combine very short exchanges into one scene. Aim for 2-5 scenes per chunk. Use the EXACT timestamps you see in the transcript.

MOVIE: {title}

TRANSCRIPT (with timestamps):
{text}

Respond with ONLY valid JSON in this exact format (no markdown, no code fences):
{{
  "scenes": [
    {{
      "start_time": "HH:MM:SS",
      "end_time": "HH:MM:SS",
      "summary": "What happens in this scene",
      "flags": {{
        "violence": 0, "blood_gore": 0, "self_harm": 0, "suicide": 0,
        "gun_weapon": 0, "abuse": 0, "death_grief": 0, "sexual_content": 0,
        "bullying": 0, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 0
      }}
    }}
  ]
}}"""

SUMMARY_PROMPT = """You are a media-safety content analyst. Based on this movie's overall content flags, write a plain-language safety summary for parents (3-5 sentences). Mention the most significant content concerns, what age group it's appropriate for, and any specific scenes to be aware of.

MOVIE: {title} ({year}) — Rated {mpaa_rating}
SYNOPSIS: {synopsis}

OVERALL FLAGS (none/mild/moderate/intense):
{flags_text}

SCENE SUMMARIES:
{segment_summaries}

Write the summary as a clear, helpful paragraph for parents. No JSON — just the text."""


def _format_srt_with_timestamps(entries, start_idx: int, end_idx: int, max_chars: int = 8000) -> str:
    """Format SRT entries with their timestamps for GPT, within a character limit."""
    lines = []
    total = 0
    for entry in entries[start_idx:end_idx]:
        h1 = int(entry.start_seconds // 3600)
        m1 = int((entry.start_seconds % 3600) // 60)
        s1 = int(entry.start_seconds % 60)
        ts = f"{h1:02d}:{m1:02d}:{s1:02d}"
        line = f"[{ts}] {entry.text}"
        if total + len(line) > max_chars:
            lines.append("[... truncated ...]")
            break
        lines.append(line)
        total += len(line) + 1
    return "\n".join(lines)


def _intensity_to_severity(max_val: int) -> str:
    """Convert max intensity value (0-5) → severity string."""
    if max_val == 0:
        return "none"
    elif max_val <= 2:
        return "mild"
    elif max_val <= 3:
        return "moderate"
    else:
        return "intense"


def _parse_gpt_json(content: str) -> dict | None:
    """Parse GPT response as JSON, stripping markdown fences if present."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


async def detect_scenes_in_chunk(title: str, entries, start_idx: int, end_idx: int) -> list[dict]:
    """Send a chunk of timestamped transcript to GPT to identify real scenes."""
    text = _format_srt_with_timestamps(entries, start_idx, end_idx)

    prompt = SCENE_DETECTION_PROMPT.format(title=title, text=text)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )

    result = _parse_gpt_json(response.choices[0].message.content)
    if not result or "scenes" not in result:
        return []

    return result["scenes"]


def aggregate_overall_flags(segments: list[dict]) -> dict:
    """Aggregate segment-level flags into overall movie flags."""
    overall = {}
    for flag in CONTENT_FLAGS:
        max_intensity = max(
            (seg["flags"].get(flag, 0) for seg in segments), default=0
        )
        overall[flag] = _intensity_to_severity(max_intensity)
    return overall


async def analyze_movie(movie_id: str) -> dict:
    """
    Full analysis pipeline:
    1. Fetch movie + transcript from Supabase
    2. Parse SRT entries
    3. Send transcript in chunks to GPT for scene detection with exact timestamps
    4. Aggregate overall flags
    5. Generate plain-language summary
    6. Update Supabase
    """
    # 1. Fetch movie
    result = supabase.table("movies").select("*").eq("id", movie_id).execute()
    if not result.data:
        raise ValueError(f"Movie {movie_id} not found")

    movie = result.data[0]
    transcript = movie.get("transcript_content", "")
    if not transcript:
        raise ValueError(f"Movie {movie['title']} has no transcript")

    print(f"\n🎬 Analyzing: {movie['title']} ({movie['year']})")

    # 2. Parse SRT
    entries = parse_srt(transcript)
    print(f"  📝 Parsed {len(entries)} subtitle entries")

    if not entries:
        raise ValueError(f"No subtitle entries parsed for {movie['title']}")

    # 3. Chunk entries and detect scenes in each chunk
    # Process ~200 subtitle entries at a time (~8-12 minutes of content)
    chunk_size = 200
    all_scenes = []

    for i in range(0, len(entries), chunk_size):
        end_i = min(i + chunk_size, len(entries))
        chunk_num = (i // chunk_size) + 1
        total_chunks = (len(entries) + chunk_size - 1) // chunk_size
        print(f"  🔍 Detecting scenes in chunk {chunk_num}/{total_chunks} (entries {i+1}–{end_i})")

        scenes = await detect_scenes_in_chunk(movie["title"], entries, i, end_i)
        all_scenes.extend(scenes)

    # Number the segments sequentially
    segments = []
    for idx, scene in enumerate(all_scenes, 1):
        segments.append({
            "segment_id": idx,
            "start_time": scene.get("start_time", "00:00:00"),
            "end_time": scene.get("end_time", "00:00:00"),
            "summary": scene.get("summary", ""),
            "flags": scene.get("flags", {flag: 0 for flag in CONTENT_FLAGS}),
        })

    print(f"  🎬 Detected {len(segments)} scenes total")

    # 4. Aggregate overall flags
    overall_flags = aggregate_overall_flags(segments)
    print(f"  🏷️  Overall flags: {overall_flags}")

    # 5. Generate plain-language summary
    flags_text = "\n".join(f"  {flag}: {severity}" for flag, severity in overall_flags.items())
    segment_summaries = "\n".join(
        f"  [{s['start_time']}–{s['end_time']}] {s['summary']}" for s in segments
    )

    summary_prompt = SUMMARY_PROMPT.format(
        title=movie["title"],
        year=movie["year"],
        mpaa_rating=movie.get("mpaa_rating", "NR"),
        synopsis=movie.get("synopsis", ""),
        flags_text=flags_text,
        segment_summaries=segment_summaries,
    )

    summary_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": summary_prompt}],
        temperature=0.4,
        max_tokens=400,
    )
    plain_summary = summary_response.choices[0].message.content.strip()
    print(f"  📋 Summary generated ({len(plain_summary)} chars)")

    # 6. Update Supabase
    update_data = {
        "overall_flags": overall_flags,
        "segments": segments,
        "plain_language_summary": plain_summary,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    supabase.table("movies").update(update_data).eq("id", movie_id).execute()
    print(f"  ✅ Movie updated in Supabase!")

    return {
        "movie_id": movie_id,
        "title": movie["title"],
        "segments_analyzed": len(segments),
        "overall_flags": overall_flags,
        "plain_language_summary": plain_summary,
    }
