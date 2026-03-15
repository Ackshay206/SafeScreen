"""
viewing_plan.py
---------------
Generates a personalised viewing plan by matching scene-level
content flags (produced by teammate's analysis.py) against a
child's sensitivity profile.

Uses Groq (Llama 3.3 70B, free) for the plan narration step.
Does NOT touch or replace any of the existing analysis service.
"""

import os
import json
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client  = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
GROQ_MODEL   = "llama-3.3-70b-versatile"

CONTENT_FLAGS = [
    "violence", "blood_gore", "self_harm", "suicide", "gun_weapon", "abuse",
    "death_grief", "sexual_content", "bullying", "substance_use",
    "flash_seizure", "loud_sensory",
]

# questionnaire slider 1-5 → max scene flag score (0-5) allowed
SLIDER_TO_MAX_FLAG = {1: 0, 2: 1, 3: 2, 4: 3, 5: 5}


def _check_scene_against_profile(
    scene_flags: dict,
    sensitivities: dict
) -> list[str]:
    """
    Returns list of flag names that breach the child's thresholds.
    Empty list means scene is safe for this child.
    """
    breached = []
    for flag in CONTENT_FLAGS:
        scene_score = scene_flags.get(flag, 0)
        user_rating = sensitivities.get(flag, 3)
        max_allowed = SLIDER_TO_MAX_FLAG.get(int(user_rating), 2)
        if scene_score > max_allowed:
            breached.append(flag)
    return breached


def _decide_action(
    breached_flags: list[str],
    handling_prefs: dict,
    default_action: str = "warn"
) -> str:
    """
    Picks the strictest action from the user's handling preferences
    across all breached flags.
    Priority: skip > blur > pause > warn
    """
    priority = ["skip", "blur", "pause", "warn"]
    chosen   = default_action

    for action in priority:
        for flag in breached_flags:
            if handling_prefs.get(flag) == action:
                return action

    return chosen


def generate_viewing_plan(segments: list[dict], profile: dict) -> dict:
    """
    Core logic — no LLM needed here.
    Matches scene flags against child profile deterministically.

    Parameters
    ----------
    segments : list of scene dicts from Supabase (produced by teammate's analysis)
               each has: segment_id, start_time, end_time, summary, flags
    profile  : {
        sensitivities    : {flag_key: 1-5},
        calming_strategy : str,
        handling_prefs   : {flag_key: "skip"|"blur"|"warn"|"pause"}
      }

    Returns
    -------
    dict with safe_segments, flagged_segments, overall_safety, counts
    """
    sensitivities    = profile.get("sensitivities", {})
    calming_strategy = profile.get("calming_strategy", "Take a short break and breathe.")
    handling_prefs   = profile.get("handling_prefs", {})

    safe_segments    = []
    flagged_segments = []

    for seg in segments:
        scene_flags = seg.get("flags", {})
        breached    = _check_scene_against_profile(scene_flags, sensitivities)

        if breached:
            action = _decide_action(breached, handling_prefs)
            flagged_segments.append({
                "segment_id"    : seg["segment_id"],
                "start_time"    : seg["start_time"],
                "end_time"      : seg["end_time"],
                "summary"       : seg["summary"],
                "breached_flags": breached,
                "action"        : action,
                "calming_tip"   : calming_strategy if action in ["pause", "warn"] else None,
            })
        else:
            safe_segments.append({
                "segment_id": seg["segment_id"],
                "start_time": seg["start_time"],
                "end_time"  : seg["end_time"],
                "summary"   : seg["summary"],
            })

    # overall safety rating
    total         = max(len(segments), 1)
    flagged_ratio = len(flagged_segments) / total

    if flagged_ratio == 0:
        overall_safety = "safe"
    elif flagged_ratio < 0.3:
        overall_safety = "caution"
    else:
        overall_safety = "not_recommended"

    return {
        "total_scenes"    : len(segments),
        "safe_scenes"     : len(safe_segments),
        "flagged_scenes"  : len(flagged_segments),
        "overall_safety"  : overall_safety,
        "safe_segments"   : safe_segments,
        "flagged_segments": flagged_segments,
    }


async def generate_plan_with_narration(
    movie_title: str,
    segments: list[dict],
    profile: dict
) -> dict:
    """
    Generates the viewing plan AND adds a Groq-written plain-language
    summary explaining the plan to the parent in simple terms.
    """
    plan = generate_viewing_plan(segments, profile)

    # build Groq narration
    child_name       = profile.get("child_name", "your child")
    calming_strategy = profile.get("calming_strategy", "a short break")
    flagged          = plan["flagged_segments"]

    if not groq_client or not flagged:
        plan["parent_summary"] = (
            f"This movie is {plan['overall_safety'].replace('_', ' ')} for {child_name}. "
            f"{plan['flagged_scenes']} of {plan['total_scenes']} scenes need attention."
        )
        return plan

    flagged_lines = "\n".join([
        f"  [{s['start_time']}–{s['end_time']}] {s['summary']} "
        f"→ {s['action'].upper()} (triggers: {', '.join(s['breached_flags'])})"
        for s in flagged[:10]   # cap at 10 to stay within token limit
    ])

    prompt = f"""Write a short plain-language viewing plan summary for a parent (3-4 sentences).

Movie: {movie_title}
Child: {child_name}
Overall safety: {plan['overall_safety']}
Flagged scenes ({plan['flagged_scenes']} of {plan['total_scenes']}):
{flagged_lines}
Calming strategy for this child: {calming_strategy}

Tell the parent what to watch out for, when to pause or skip, and remind them of the calming strategy. Be warm and practical. No bullet points — just a short paragraph."""

    try:
        response = groq_client.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = [{"role": "user", "content": prompt}],
            temperature = 0.4,
            max_tokens  = 300,
        )
        plan["parent_summary"] = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq narration error: {e}")
        plan["parent_summary"] = (
            f"This movie is {plan['overall_safety'].replace('_', ' ')} for {child_name}. "
            f"{plan['flagged_scenes']} scenes need attention."
        )

    return plan