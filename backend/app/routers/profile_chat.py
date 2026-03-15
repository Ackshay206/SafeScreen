import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

from app.models.child_profile import ProfileCreate

router = APIRouter(prefix="/api/profile_chat", tags=["profile_chat"])

# You will need to make sure GEMINI_API_KEY is available in your env variables.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
    is_complete: bool
    profile_data: dict | None = None


SYSTEM_INSTRUCTION = """
You are a friendly, empathetic assistant helping a user set up a media sensitivity profile for themselves or their child.
The ultimate goal is to generate a JSON payload with specific sensitivities, age, name, calming strategy, and contextual answers.

Guidelines:
1. Act naturally, keep your messages short and conversational.
2. If some questions can be deduced or answered together, don't drag it out.

PHASE 1: Core Questions
You must gather the following if not already provided:
- Name of the person the profile is for.
- Their age as a number.
- Their general sensitivities on a scale of 1-5 (5 = highly sensitive/low tolerance, 1 = not sensitive/high tolerance). Specifically ask about things like violence, blood/gore, self-harm, suicide, gun/weapon, abuse, death/grief, sexual content, bullying, substance use, flash/seizure, loud/sensory. To make it conversational, ask them to list their main concerns first. If they leave any out, assume a default of 3 (moderate) unless context suggests otherwise.
- A calming strategy (e.g., breathing, counting, looking at cute animals).

PHASE 2: Adaptive Context (Crucial!)
Once you know their age and main sensitivities, ask up to 3 specific follow-up questions to understand NUANCE.
For example, if Age = 7 and sensitive to Violence, ask "Are they okay with slapstick or cartoon violence (like Tom & Jerry)?"
If sensitive to Death/Grief, ask "How do they handle the death of an animal vs a human character?"
The above questions are just examples, you can ask other questions based on the user's age and other responses. You can ask a maximum of 3 extra questions. 
Keep these to 1 or 2 questions at a time. The goal is to collect qualitative data that will be stored in `additional_details`.

PHASE 3: Completion
Once you have gathered all necessary information (Phase 1 core info + Phase 2 additional details), you must output a FINAL message.
When you are ready to conclude, output EXACTLY AND ONLY a valid JSON object starting with ```json and ending with ``` (no other conversational text in your final response).

The final JSON output MUST have exactly this structure:
{
    "name": "string",
    "age": number,
    "sensitivities": {
        "violence": number,
        "blood_gore": number,
        "self_harm": number,
        "suicide": number,
        "gun_weapon": number,
        "abuse": number,
        "death_grief": number,
        "sexual_content": number,
        "bullying": number,
        "substance_use": number,
        "flash_seizure": number,
        "loud_sensory": number
    },
    "calming_strategy": "string",
    "additional_details": "string (a helpful paragraph summarizing the answers to the 5 adaptive questions)"
}

DO NOT include conversational text outside the JSON block when you deliver the JSON. Only deliver the JSON when you have finished Phase 1 and Phase 2.
"""

@router.post("", response_model=ChatResponse)
async def chat_with_profile_assistant(request: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")

    if not request.messages:
        # Initial greeting
        messages = [
            types.Content(role="user", parts=[types.Part(text="Hello, I'd like to set up a new profile.")]),
        ]
    else:
        # Convert frontend messages to Gemini format
        messages = []
        for msg in request.messages:
            role = "user" if msg.role == "user" else "model"
            messages.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            )
        )
        reply_text = response.text.strip()
        
        # Check if the LLM output the final JSON
        if reply_text.startswith("```json") and reply_text.endswith("```"):
            json_str = reply_text[7:-3].strip()
            try:
                profile_data = json.loads(json_str)
                return ChatResponse(
                    reply="All set! I've created the profile.",
                    is_complete=True,
                    profile_data=profile_data
                )
            except json.JSONDecodeError:
                pass # Fall back to treating it as regular text if parsing fails
        elif reply_text.startswith("{") and reply_text.endswith("}"):
            try:
                profile_data = json.loads(reply_text)
                return ChatResponse(
                    reply="All set! I've created the profile.",
                    is_complete=True,
                    profile_data=profile_data
                )
            except json.JSONDecodeError:
                pass

        return ChatResponse(
            reply=reply_text,
            is_complete=False,
            profile_data=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))