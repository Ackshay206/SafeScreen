"""
feedback.py
-----------
Generates personalised calming/decompression YouTube video
suggestions based on the viewer's calming strategy from their profile.
Uses Gemini 2.5 Flash to interpret the strategy and generate
relevant YouTube search links.
"""

import os
import json
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

CALMING_VIDEOS_PROMPT = """You are a wellness assistant for SafeScreen, a media safety platform.

A viewer just finished watching a movie and reported some emotional discomfort. Based on their personal calming strategy and what triggered them, suggest 5 specific YouTube video search queries that would help them decompress.

VIEWER INFO:
- Name: {viewer_name}
- Age: {age}
- Calming Strategy: {calming_strategy}
- Content that triggered them: {triggered_content}
- Their feedback: {feedback_note}
- Distress level: {distress_level}

RULES:
1. Tailor suggestions to their stated calming strategy. If they like "breathing exercises", suggest specific breathing technique videos. If they like "looking at cute animals", suggest specific animal compilations.
2. Consider their AGE. A 6-year-old needs different content than a 30-year-old.
3. If they reported distress, include at least one grounding/mindfulness video.
4. Make search queries specific enough to find good results (e.g., "4-7-8 breathing exercise guided 5 minutes" not just "breathing").
5. Include a mix — some directly related to their calming strategy, some general decompression.

Return ONLY valid JSON (no markdown, no fences):
{{
  "videos": [
    {{
      "title": "Human-readable title describing the video",
      "search_query": "The exact YouTube search query",
      "youtube_url": "https://www.youtube.com/results?search_query=URL+encoded+query",
      "reason": "Why this was suggested (1 sentence)"
    }}
  ]
}}
"""

FALLBACK_VIDEOS = {
    "breathing": [
        {"title": "5-Minute Guided Breathing Exercise", "search_query": "guided breathing exercise 5 minutes calm", "youtube_url": "https://www.youtube.com/results?search_query=guided+breathing+exercise+5+minutes+calm", "reason": "A short guided breathing session to help you relax."},
        {"title": "Box Breathing Technique", "search_query": "box breathing technique 4 4 4 4 guided", "youtube_url": "https://www.youtube.com/results?search_query=box+breathing+technique+4+4+4+4+guided", "reason": "Box breathing is a proven method to calm your nervous system."},
        {"title": "Deep Breathing for Stress Relief", "search_query": "deep breathing stress relief relaxation", "youtube_url": "https://www.youtube.com/results?search_query=deep+breathing+stress+relief+relaxation", "reason": "A simple deep breathing practice for stress relief."},
    ],
    "animals": [
        {"title": "Cute Baby Animals Compilation", "search_query": "cute baby animals compilation relaxing", "youtube_url": "https://www.youtube.com/results?search_query=cute+baby+animals+compilation+relaxing", "reason": "Adorable animals to lift your mood."},
        {"title": "Funny Cat Videos", "search_query": "funny cat videos compilation 2025", "youtube_url": "https://www.youtube.com/results?search_query=funny+cat+videos+compilation+2025", "reason": "Cat videos are proven mood boosters."},
        {"title": "Puppy Videos Relaxing", "search_query": "cute puppy videos relaxing happy", "youtube_url": "https://www.youtube.com/results?search_query=cute+puppy+videos+relaxing+happy", "reason": "Puppies to help you feel better."},
    ],
    "music": [
        {"title": "Relaxing Piano Music", "search_query": "relaxing piano music calm stress relief 10 minutes", "youtube_url": "https://www.youtube.com/results?search_query=relaxing+piano+music+calm+stress+relief+10+minutes", "reason": "Soothing piano music for decompression."},
        {"title": "Lofi Beats to Relax", "search_query": "lofi beats relax chill study", "youtube_url": "https://www.youtube.com/results?search_query=lofi+beats+relax+chill+study", "reason": "Gentle lofi music to ease your mind."},
        {"title": "Nature Sounds with Music", "search_query": "nature sounds relaxing music rain forest", "youtube_url": "https://www.youtube.com/results?search_query=nature+sounds+relaxing+music+rain+forest", "reason": "A blend of nature sounds and music for calm."},
    ],
    "default": [
        {"title": "Calming Nature Sounds", "search_query": "calming nature sounds relaxation 10 minutes", "youtube_url": "https://www.youtube.com/results?search_query=calming+nature+sounds+relaxation+10+minutes", "reason": "Nature sounds for gentle decompression."},
        {"title": "Guided Mindfulness Meditation", "search_query": "guided mindfulness meditation 5 minutes beginner", "youtube_url": "https://www.youtube.com/results?search_query=guided+mindfulness+meditation+5+minutes+beginner", "reason": "A short mindfulness session to recenter yourself."},
        {"title": "Relaxing Music for Stress Relief", "search_query": "relaxing music stress relief calm piano", "youtube_url": "https://www.youtube.com/results?search_query=relaxing+music+stress+relief+calm+piano", "reason": "Soothing music to help you unwind."},
        {"title": "Progressive Muscle Relaxation", "search_query": "progressive muscle relaxation guided audio", "youtube_url": "https://www.youtube.com/results?search_query=progressive+muscle+relaxation+guided+audio", "reason": "Release physical tension held from watching."},
        {"title": "Positive Affirmations", "search_query": "positive affirmations calm anxiety short", "youtube_url": "https://www.youtube.com/results?search_query=positive+affirmations+calm+anxiety+short", "reason": "Gentle affirmations to restore a sense of safety."},
    ],
}


def _get_fallback_videos(calming_strategy: str) -> list[dict]:
    """Return fallback videos based on keyword matching in calming strategy."""
    strategy_lower = calming_strategy.lower()
    videos = []

    if any(w in strategy_lower for w in ["breath", "breathing", "inhale", "exhale"]):
        videos.extend(FALLBACK_VIDEOS["breathing"])
    if any(w in strategy_lower for w in ["animal", "cat", "dog", "puppy", "kitten", "cute"]):
        videos.extend(FALLBACK_VIDEOS["animals"])
    if any(w in strategy_lower for w in ["music", "song", "piano", "lofi", "melody"]):
        videos.extend(FALLBACK_VIDEOS["music"])

    if not videos:
        videos = FALLBACK_VIDEOS["default"]

    return videos[:5]


async def generate_calming_videos(
    viewer_name: str,
    age: int | None,
    calming_strategy: str,
    triggered_content: list[str],
    feedback_note: str,
    distress_level: str,
) -> list[dict]:
    """
    Generate personalised YouTube video suggestions based on the
    viewer's calming strategy and what triggered them.
    """
    if not gemini_client:
        return _get_fallback_videos(calming_strategy)

    triggered_str = ", ".join(triggered_content) if triggered_content else "general discomfort"

    prompt = CALMING_VIDEOS_PROMPT.format(
        viewer_name=viewer_name,
        age=age or "unknown",
        calming_strategy=calming_strategy,
        triggered_content=triggered_str,
        feedback_note=feedback_note or "No additional notes.",
        distress_level=distress_level,
    )

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=types.GenerateContentConfig(
                temperature=0.5,
            )
        )

        raw = response.text.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        data = json.loads(raw)
        videos = data.get("videos", [])

        valid = []
        for v in videos:
            if all(k in v for k in ("title", "search_query", "youtube_url", "reason")):
                valid.append(v)
        return valid[:5] if valid else _get_fallback_videos(calming_strategy)

    except Exception as e:
        print(f"Calming videos generation error: {e}")
        return _get_fallback_videos(calming_strategy)