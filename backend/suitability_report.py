import os
import sys
import json
sys.path.append(os.getcwd())

from app.database import supabase

# Mapping for intensities
SCORE = {"none": 0, "mild": 2, "moderate": 3, "intense": 5}

def check_suitability(m):
    flags = m.get("overall_flags", {})
    # Get values
    blood = flags.get("blood_gore", "none")
    gun = flags.get("gun_weapon", "none")
    bullying = flags.get("bullying", "none")
    
    blood_score = SCORE.get(blood, 0)
    gun_score = SCORE.get(gun, 0)
    
    # User Profile: Blood 5 (<=2), Gun 4 (<=3)
    blood_pass = blood_score <= 2
    gun_pass = gun_score <= 3
    
    return {
        "title": m["title"],
        "blood": blood,
        "gun": gun,
        "bullying": bullying,
        "blood_pass": blood_pass,
        "gun_pass": gun_pass,
        "overall_pass": blood_pass and gun_pass
    }

try:
    res = supabase.table("movies").select("title, overall_flags").execute()
    report = [check_suitability(m) for m in res.data]
    print(json.dumps(report, indent=2))
except Exception as e:
    print(f"Error: {e}")
