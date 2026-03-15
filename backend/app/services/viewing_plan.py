"""
viewing_plan.py
---------------
Generates a fully AI-powered personalised viewing plan using
Gemini 2.5 Pro. The entire profile, movie data, scene segments,
and rule guidelines are passed to the LLM to produce a
comprehensive viewing plan.

Works for ALL age groups — children, teens, and adults.
The LLM adapts its recommendations based on the viewer's age,
individual sensitivities, and personal context.
"""

import os
import json
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_INSTRUCTION = """
You are SafeScreen, an expert media safety analyst. You generate personalised viewing plans for movies based on an individual viewer's sensitivity profile. You serve ALL age groups — children, teenagers, adults, and elderly viewers. Every person deserves a comfortable viewing experience tailored to their unique needs.

You will receive:
1. Full movie data (title, year, rating, synopsis, overall content flags, and scene-by-scene segments with timestamps and flags)
2. Full viewer profile (name, age, sensitivity levels 1-5 for 12 categories, calming strategy, and additional contextual details)

### SENSITIVITY SCALE (from the viewer's profile):
- 1 = Not Sensitive (high tolerance, content does not bother them)
- 2 = Slightly Sensitive (minor discomfort, can handle with awareness)
- 3 = Moderate (noticeable discomfort, benefits from preparation)
- 4 = Sensitive (significant discomfort, needs active mitigation)
- 5 = Very Sensitive (cannot tolerate, must avoid entirely)

### ACTION GUIDELINES (use as baseline, apply your judgment based on full context):
When a scene contains a flagged content type, choose an action based on the viewer's sensitivity:

- **Sensitivity 5 (Very Sensitive)** → `skip` — Skip this segment entirely. The content is too distressing for this viewer.
- **Sensitivity 4 (Sensitive)** → `blur` for primarily visual content (violence, blood_gore, self_harm, suicide, gun_weapon, abuse, sexual_content, flash_seizure) OR `mute` for primarily audio-driven content (loud_sensory, substance_use dialogue/references). Active mitigation needed.
- **Sensitivity 3 (Moderate)** → `pause_and_prompt` — Pause before this scene. For children/teens: parent presence recommended. For adults: a heads-up notification so the viewer can mentally prepare or choose to have a companion present.
- **Sensitivity 2 (Slightly Sensitive)** → `parent_present` for minors (under 18) OR `viewer_discretion` for adults. Content is manageable but awareness helps.
- **Sensitivity 1 (Not Sensitive)** → `continue` — Safe to watch normally. No action needed.

### AGE-ADAPTIVE RULES:

**Children (under 13):**
- Err on the side of caution. If a decision is borderline, choose the stricter action.
- Always recommend parent/guardian co-viewing for any flagged content.
- Session lengths should be 30-40 minutes max.
- Use warm, child-appropriate language in parent prompts.
- Even "mild" flags may warrant attention for very young children (under 7).

**Teenagers (13-17):**
- Moderate caution. Teens can handle more context and preparation.
- Parent co-viewing is suggested (not required) for moderate flags.
- Session lengths can be 45-90 minutes.
- Parent prompts should acknowledge the teen's growing autonomy while flagging genuine concerns.
- Consider MPAA rating context — a 16-year-old watching a PG-13 movie needs less intervention than a 13-year-old watching an R-rated one.

**Adults (18-64):**
- Respect autonomy. Adults choose what to watch, but sensitivities are real and valid.
- Instead of "parent present", use "companion recommended" or "viewer discretion" for levels 2-3.
- Skip and blur/mute still apply for sensitivities 4-5 — these represent genuine distress triggers (PTSD, phobias, trauma responses, medical conditions like epilepsy).
- Session splitting is only needed if the viewer has a medical/sensory condition (flash_seizure, loud_sensory at high sensitivity) or if flagged content is extremely dense.
- Language should be respectful and non-patronizing. Adults with high sensitivity to violence may be trauma survivors; adults with flash_seizure sensitivity may have epilepsy.

**Elderly (65+):**
- Similar to adults but with extra attention to sensory sensitivities (flash_seizure, loud_sensory).
- Consider that some elderly viewers may have hearing or vision conditions that interact with content.
- Session pacing may benefit from shorter sessions (60 min max) for comfort.

### CRITICAL NUANCE RULES:
- When multiple flags exist in one segment, use the STRICTEST action required by any of them.
- The "additional_details" field contains qualitative context gathered during profile setup. This is EXTREMELY important. Examples:
  - "Okay with cartoon violence but not realistic violence" → differentiate based on movie genre/style
  - "Combat veteran, avoid gunfire sounds" → mute gun_weapon scenes even at sensitivity 3
  - "Has epilepsy" → always skip flash_seizure regardless of stated sensitivity
  - "Recovering from loss of parent" → extra sensitivity around death_grief scenes
  - "Generally fine with horror but hates jump scares" → focus on loud_sensory, not overall horror
  - "Watching to overcome fear gradually" → maybe use pause_and_prompt instead of skip to support exposure therapy (but never push)
- Use the movie's MPAA rating and synopsis to understand the TONE of flags. "Violence" in a Pixar movie is very different from "violence" in a Saw movie.
- Consider cumulative impact — 3 consecutive flagged segments are harder than 3 spread across the movie. Recommend breaks between clusters.

### SESSION PACING RULES:
- If more than 30% of segments are flagged (non-continue), recommend splitting into sessions.
- Place session breaks at natural narrative pauses — after safe segments, between acts, or after emotionally intense sequences.
- Age-based session length guidelines:
  - Under 7: 20-30 minutes
  - 7-12: 30-45 minutes  
  - 13-17: 45-90 minutes
  - 18-64: Full movie unless heavily flagged or viewer has sensory conditions
  - 65+: 45-60 minutes for comfort
- If the movie is short (under 90 min) and lightly flagged, a single session is fine for all ages.

### OVERALL MODE (choose one):
- `safe` — No meaningful flags triggered. Watch freely.
- `minor_caution` — Very few flags, mostly "continue" or low-level actions. Minimal risk.
- `co_view_suggested` — (For minors) Some flagged content, parent/guardian should ideally be present. (For adults) Some content may be uncomfortable, companion viewing optional.
- `co_view_required` — (For minors) Parent/guardian must be present throughout. (For adults) Significant triggers present, strongly recommend not watching alone if sensitivities are high.
- `heavy_modification` — Many segments need skipping/blurring. The viewing experience will be significantly altered. Consider whether an alternative movie might be more enjoyable.
- `not_recommended` — This movie fundamentally conflicts with the viewer's sensitivity profile. Too many severe triggers. Strongly suggest choosing a different movie.

### OUTPUT FORMAT:
Return ONLY valid JSON (no markdown, no code fences, no extra text) with this exact structure:

{
  "overall_mode": {
    "mode": "safe|minor_caution|co_view_suggested|co_view_required|heavy_modification|not_recommended",
    "co_viewing": true/false,
    "description": "A 1-2 sentence explanation of the overall safety verdict, written appropriately for the viewer's age group."
  },
  "parent_summary": "A warm, practical 4-6 sentence paragraph. For minors: address the parent/guardian. For adults: address the viewer directly. Explain the plan, what to watch for, when to use the calming strategy, and session recommendations.",
  "sessions": [
    {
      "session": 1,
      "start_segment": 1,
      "end_segment": 10,
      "start_time": "00:00:00",
      "end_time": "00:45:00",
      "is_checkpoint": true/false,
      "checkpoint_message": "Message shown when pausing between sessions. Warm and encouraging. Null if last session.",
      "flagged_count": 2,
      "total_count": 10
    }
  ],
  "segment_actions": [
    {
      "segment_id": 1,
      "start_time": "00:00:00",
      "end_time": "00:05:30",
      "summary": "Original scene summary from the data",
      "overall_action": "continue|skip|blur|mute|pause_and_prompt|parent_present",
      "action_description": "Human-readable description of what to do, written for the appropriate age group",
      "triggered_flags": ["violence", "gun_weapon"],
      "flag_details": [
        {
          "flag": "violence",
          "sensitivity": 4,
          "action": "blur",
          "description": "Blur the screen during this segment"
        }
      ],
      "parent_prompt": "For minors: 'Parent presence recommended for next 3 minutes.' For adults: 'Heads up: the next 3 minutes contain intense violence.' Null if safe.",
      "calming_tip": "The calming strategy text, or null if safe",
      "is_safe": true/false
    }
  ]
}

CRITICAL RULES:
- Every segment from the input MUST appear in segment_actions. Do not skip any. Safe segments should have overall_action "continue" and is_safe true.
- For adults (18+), replace "Parent presence recommended" language with "Viewer advisory" or "Heads up" language.
- For the parent_present action with adults, use the description "Viewer discretion advised" or "Consider watching with a companion" instead.
- Be genuine and thoughtful. A person's sensitivities are deeply personal — whether they stem from childhood fears, trauma, medical conditions, or personal preference. Treat every profile with respect.
"""

ACTION_DESCRIPTIONS = {
    "skip": "Skip this segment entirely",
    "blur": "Blur the screen during this segment",
    "mute": "Mute audio during this segment",
    "pause_and_prompt": "Pause and prepare — sensitive content ahead",
    "parent_present": "Co-viewing recommended for this segment",
    "continue": "Safe to watch normally",
}

ACTION_SEVERITY = {
    "skip": 6, "blur": 5, "mute": 4,
    "pause_and_prompt": 3, "parent_present": 2, "continue": 1,
}


def _build_gemini_prompt(movie: dict, segments: list[dict], profile: dict) -> str:
    """Build the full prompt with all movie + profile data for Gemini."""

    # Movie info
    overall_flags = movie.get("overall_flags", {})
    flags_summary = ", ".join(
        f"{k.replace('_', ' ').title()}: {v.upper()}"
        for k, v in overall_flags.items() if v != "none"
    ) or "CLEAN — no flags detected"

    # Profile info
    sensitivities = profile.get("sensitivities", {})
    sens_lines = "\n".join(
        f"  {k.replace('_', ' ').title()}: {v}/5"
        for k, v in sensitivities.items()
    )

    # Determine viewer category for context
    age = profile.get("age")
    age_category = "unknown"
    if age is not None:
        try:
            age_int = int(age)
            if age_int < 7:
                age_category = "young child (under 7)"
            elif age_int < 13:
                age_category = "child (7-12)"
            elif age_int < 18:
                age_category = "teenager (13-17)"
            elif age_int < 65:
                age_category = "adult (18-64)"
            else:
                age_category = "elderly (65+)"
        except (ValueError, TypeError):
            pass

    # High sensitivity warnings
    high_sens = [
        k.replace('_', ' ').title()
        for k, v in sensitivities.items()
        if v and int(v) >= 4
    ]
    high_sens_warning = ""
    if high_sens:
        high_sens_warning = f"\n⚠️ HIGH SENSITIVITY TRIGGERS: {', '.join(high_sens)} — these require the strictest actions.\n"

    # Segments
    seg_lines = []
    for seg in segments:
        flags = seg.get("flags", [])
        if isinstance(flags, dict):
            flags = [k for k, v in flags.items() if v and v != "none"]
        flag_str = ", ".join(flags) if flags else "NONE"
        seg_lines.append(
            f"  Segment {seg.get('segment_id', '?')}: "
            f"[{seg.get('start_time', '?')} – {seg.get('end_time', '?')}] "
            f"| Flags: [{flag_str}] "
            f"| Summary: {seg.get('summary', 'No summary')}"
        )

    additional = profile.get("additional_details", "")
    additional_section = ""
    if additional and additional.strip():
        additional_section = f"""
ADDITIONAL CONTEXT ABOUT THIS VIEWER (very important — use this for nuanced decisions):
{additional}
"""

    prompt = f"""Generate a complete viewing plan for the following movie and viewer profile.

═══ MOVIE DATA ═══
Title: {movie.get('title', 'Unknown')}
Year: {movie.get('year', '?')}
MPAA Rating: {movie.get('mpaa_rating', 'NR')}
Runtime: {movie.get('runtime_minutes', '?')} minutes
Genres: {', '.join(movie.get('genre', []))}
Synopsis: {movie.get('synopsis', 'No synopsis available.')}

Overall Content Flags: {flags_summary}

Plain Language Safety Summary:
{movie.get('plain_language_summary', 'No summary available.')}

═══ SCENE SEGMENTS ({len(segments)} total) ═══
{chr(10).join(seg_lines)}

═══ VIEWER PROFILE ═══
Name: {profile.get('child_name', 'Unknown')}
Age: {age} ({age_category})
Viewer Category: {age_category}

Sensitivity Levels (1=Not Sensitive, 5=Very Sensitive):
{sens_lines}
{high_sens_warning}
Calming Strategy: {profile.get('calming_strategy', 'Take a short break and breathe.')}
{additional_section}
═══ IMPORTANT CONTEXT ═══
- This viewer is a {age_category}. Tailor ALL language, actions, and recommendations appropriately.
- {"For this minor, address the parent/guardian in the parent_summary and prompts." if age and int(age) < 18 else "This is an adult viewer. Address them directly with respect and without being patronizing. Their sensitivities are valid personal preferences or medical/psychological needs."}
- Use the additional context above (if provided) to make smarter decisions than the baseline rules alone.

═══ TASK ═══
Analyze every segment against this viewer's specific sensitivity profile.
For each segment, determine the appropriate action using the guidelines.
Group segments into viewing sessions appropriate for this viewer's age and needs.
Provide a warm, age-appropriate summary.

Return ONLY the JSON object as specified in your instructions. No other text."""

    return prompt


def _parse_gemini_response(text: str) -> dict | None:
    """Parse Gemini response, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw text (first 500 chars): {text[:500]}")
        return None


def _validate_and_fix_plan(plan: dict, segments: list[dict], profile: dict) -> dict:
    """Validate the LLM output and fill in any missing segments."""
    segment_actions = plan.get("segment_actions", [])
    existing_ids = {s.get("segment_id") for s in segment_actions}

    calming = profile.get("calming_strategy", "Take a short break and breathe.")

    # Ensure every segment is present
    for seg in segments:
        seg_id = seg.get("segment_id")
        if seg_id not in existing_ids:
            segment_actions.append({
                "segment_id": seg_id,
                "start_time": seg.get("start_time", "00:00:00"),
                "end_time": seg.get("end_time", "00:00:00"),
                "summary": seg.get("summary", ""),
                "overall_action": "continue",
                "action_description": ACTION_DESCRIPTIONS["continue"],
                "triggered_flags": [],
                "flag_details": [],
                "parent_prompt": None,
                "calming_tip": None,
                "is_safe": True,
            })

    # Sort by segment_id
    segment_actions.sort(key=lambda s: s.get("segment_id", 0))

    # Ensure all segment_actions have required fields
    for sa in segment_actions:
        action = sa.get("overall_action", "continue")
        if action not in ACTION_DESCRIPTIONS:
            sa["overall_action"] = "continue"
            action = "continue"

        sa.setdefault("action_description", ACTION_DESCRIPTIONS.get(action, action))
        sa.setdefault("triggered_flags", [])
        sa.setdefault("flag_details", [])
        sa.setdefault("parent_prompt", None)
        sa.setdefault("is_safe", action == "continue")

        if not sa["is_safe"]:
            sa.setdefault("calming_tip", calming)
        else:
            sa.setdefault("calming_tip", None)

    plan["segment_actions"] = segment_actions

    # Ensure overall_mode exists
    if "overall_mode" not in plan or not isinstance(plan["overall_mode"], dict):
        plan["overall_mode"] = {
            "mode": "co_view_suggested",
            "co_viewing": True,
            "description": "Please review the segment-by-segment plan for details.",
        }

    # Compute stats
    safe_count = sum(1 for s in segment_actions if s.get("is_safe"))
    plan["total_segments"] = len(segment_actions)
    plan["safe_segments"] = safe_count
    plan["flagged_segments"] = len(segment_actions) - safe_count

    # Ensure sessions exist
    if "sessions" not in plan or not plan["sessions"]:
        plan["sessions"] = [{
            "session": 1,
            "start_segment": segment_actions[0]["segment_id"] if segment_actions else 1,
            "end_segment": segment_actions[-1]["segment_id"] if segment_actions else 1,
            "start_time": segment_actions[0].get("start_time", "00:00:00") if segment_actions else "00:00:00",
            "end_time": segment_actions[-1].get("end_time", "00:00:00") if segment_actions else "00:00:00",
            "is_checkpoint": False,
            "checkpoint_message": None,
            "flagged_count": plan["flagged_segments"],
            "total_count": plan["total_segments"],
        }]

    # Ensure parent_summary exists
    if "parent_summary" not in plan or not plan["parent_summary"]:
        mode = plan["overall_mode"]
        viewer_name = profile.get("child_name", "the viewer")
        plan["parent_summary"] = (
            f"This movie is rated as {mode.get('mode', 'unknown').replace('_', ' ')} "
            f"for {viewer_name}. "
            f"Please review the segment-by-segment plan below for detailed guidance."
        )

    # Add action_summary to overall_mode if missing
    if "action_summary" not in plan.get("overall_mode", {}):
        counts = {}
        for sa in segment_actions:
            a = sa.get("overall_action", "continue")
            counts[a] = counts.get(a, 0) + 1
        plan["overall_mode"]["action_summary"] = counts

    return plan


def _build_fallback_plan(segments: list[dict], profile: dict, movie_title: str) -> dict:
    """
    Fallback: simple rule-based plan when Gemini is unavailable.
    """
    sensitivities = profile.get("sensitivities", {})
    calming = profile.get("calming_strategy", "Take a short break and breathe.")
    viewer_name = profile.get("child_name", "the viewer")
    age = profile.get("age")

    is_minor = False
    try:
        if age and int(age) < 18:
            is_minor = True
    except (ValueError, TypeError):
        pass

    SLIDER_TO_FLAG = {
        "violence": "violence", "blood_gore": "blood_gore",
        "self_harm": "self_harm", "suicide": "suicide",
        "gun_weapon": "gun_weapon", "abuse": "abuse",
        "death_grief": "death_grief", "sexual_content": "sexual_content",
        "bullying": "bullying", "substance_use": "substance_use",
        "flash_seizure": "flash_seizure", "loud_sensory": "loud_sensory",
    }
    AUDIO_FLAGS = {"loud_sensory", "substance_use"}
    SENS_TO_ACTION = {5: "skip", 4: "blur", 3: "pause_and_prompt", 2: "parent_present", 1: "continue"}

    segment_actions = []
    for seg in segments:
        flags = seg.get("flags", [])
        if isinstance(flags, dict):
            flags = [k for k, v in flags.items() if v and v != "none"]

        triggered = []
        flag_details = []
        for f in flags:
            sk = None
            for k, v in SLIDER_TO_FLAG.items():
                if v == f:
                    sk = k
                    break
            if not sk:
                continue
            sens = int(sensitivities.get(sk, 3))
            action = SENS_TO_ACTION.get(sens, "continue")
            if sens == 4 and f in AUDIO_FLAGS:
                action = "mute"
            if action != "continue":
                triggered.append(f)
                flag_details.append({
                    "flag": f, "sensitivity": sens,
                    "action": action,
                    "description": ACTION_DESCRIPTIONS.get(action, action),
                })

        all_actions = [fd["action"] for fd in flag_details]
        overall = max(all_actions, key=lambda a: ACTION_SEVERITY.get(a, 0)) if all_actions else "continue"
        is_safe = overall == "continue"

        prompt_text = None
        if not is_safe:
            flag_labels = ", ".join(triggered)
            if is_minor:
                prompt_text = f"Parent presence recommended. Triggers: {flag_labels}."
            else:
                prompt_text = f"Viewer advisory: upcoming content includes {flag_labels}."

        segment_actions.append({
            "segment_id": seg.get("segment_id"),
            "start_time": seg.get("start_time", "00:00:00"),
            "end_time": seg.get("end_time", "00:00:00"),
            "summary": seg.get("summary", ""),
            "overall_action": overall,
            "action_description": ACTION_DESCRIPTIONS.get(overall, overall),
            "triggered_flags": triggered,
            "flag_details": flag_details,
            "parent_prompt": prompt_text,
            "calming_tip": None if is_safe else calming,
            "is_safe": is_safe,
        })

    safe_count = sum(1 for s in segment_actions if s["is_safe"])
    flagged_count = len(segment_actions) - safe_count

    return {
        "overall_mode": {
            "mode": "co_view_suggested" if flagged_count > 0 else "safe",
            "co_viewing": flagged_count > 0 and is_minor,
            "description": f"{'Some content needs attention.' if flagged_count > 0 else 'Safe to watch.'} (Generated using fallback rules — Gemini unavailable.)",
            "action_summary": {},
        },
        "parent_summary": (
            f"For {viewer_name}, \"{movie_title}\" has {flagged_count} of {len(segment_actions)} "
            f"scenes that need attention. This plan was generated using basic rules because the AI service "
            f"was unavailable. Please review each flagged segment carefully."
        ),
        "sessions": [{
            "session": 1,
            "start_segment": segment_actions[0]["segment_id"] if segment_actions else 1,
            "end_segment": segment_actions[-1]["segment_id"] if segment_actions else 1,
            "start_time": segment_actions[0]["start_time"] if segment_actions else "00:00:00",
            "end_time": segment_actions[-1]["end_time"] if segment_actions else "00:00:00",
            "is_checkpoint": False,
            "checkpoint_message": None,
            "flagged_count": flagged_count,
            "total_count": len(segment_actions),
        }],
        "segment_actions": segment_actions,
        "total_segments": len(segment_actions),
        "safe_segments": safe_count,
        "flagged_segments": flagged_count,
        "child_name": viewer_name,
        "child_age": age,
        "calming_strategy": calming,
    }


async def generate_plan_with_narration(
    movie: dict,
    segments: list[dict],
    profile: dict
) -> dict:
    """
    Main entry point. Generates a full AI-powered viewing plan using Gemini 2.5 Pro.
    Falls back to rule-based logic if Gemini is unavailable.

    Parameters
    ----------
    movie    : full movie dict from Supabase
    segments : list of scene dicts
    profile  : { child_name, age, sensitivities, calming_strategy, additional_details }
    """
    viewer_name = profile.get("child_name", "the viewer")
    age = profile.get("age")
    calming = profile.get("calming_strategy", "Take a short break and breathe.")
    movie_title = movie.get("title", "Unknown")

    if not gemini_client:
        print("WARNING: Gemini client not available. Using fallback rules.")
        return _build_fallback_plan(segments, profile, movie_title)

    prompt = _build_gemini_prompt(movie, segments, profile)

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
            )
        )

        raw_text = response.text.strip()
        plan = _parse_gemini_response(raw_text)

        if not plan:
            print("WARNING: Failed to parse Gemini response. Using fallback.")
            return _build_fallback_plan(segments, profile, movie_title)

        # Validate and fix any missing data
        plan = _validate_and_fix_plan(plan, segments, profile)

        # Attach profile metadata
        plan["child_name"] = viewer_name
        plan["child_age"] = age
        plan["calming_strategy"] = calming

        return plan

    except Exception as e:
        print(f"Gemini error: {e}")
        return _build_fallback_plan(segments, profile, movie_title)