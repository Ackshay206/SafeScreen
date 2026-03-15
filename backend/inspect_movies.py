import os
import sys
import json
sys.path.append(os.getcwd())

from app.database import supabase

def clean_print(m):
    print(json.dumps({
        "title": m["title"],
        "mpaa": m["mpaa_rating"],
        "flags": m.get("overall_flags", {}),
        "segments_count": len(m.get("segments", []))
    }, indent=2))
    print("-" * 30)

try:
    res = supabase.table("movies").select("*").execute()
    if res.data:
        for m in res.data:
            clean_print(m)
    else:
        print("No movies found.")
    
except Exception as e:
    print(f"Error: {e}")
