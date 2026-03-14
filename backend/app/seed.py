"""
Seed script: inserts sample movies into Supabase.
Run with:  python -m app.seed
"""
from datetime import datetime, timezone
from app.database import supabase


SAMPLE_MOVIES = [
    {
        "title": "The Dark Knight",
        "year": 2008,
        "genre": ["Action", "Crime", "Drama"],
        "runtime_minutes": 152,
        "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911BTUgMe1nFGDi.jpg",
        "synopsis": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
        "mpaa_rating": "PG-13",
        "transcript_file": "the_dark_knight.srt",
        "overall_flags": {
            "violence": "intense", "blood_gore": "moderate", "self_harm": "none",
            "suicide": "mild", "gun_weapon": "intense", "abuse": "moderate",
            "death_grief": "intense", "sexual_content": "none", "bullying": "moderate",
            "substance_use": "none", "flash_seizure": "mild", "loud_sensory": "intense",
        },
        "segments": [
            {"segment_id": 1, "start_time": "00:00:00", "end_time": "00:05:00",
             "summary": "Bank heist sequence — masked robbers storm a bank with guns, multiple characters are killed.",
             "flags": {"violence": 5, "blood_gore": 2, "self_harm": 0, "suicide": 0, "gun_weapon": 5, "abuse": 0, "death_grief": 3, "sexual_content": 0, "bullying": 0, "substance_use": 0, "flash_seizure": 1, "loud_sensory": 4}},
            {"segment_id": 2, "start_time": "00:05:00", "end_time": "00:15:00",
             "summary": "Bruce Wayne at a fundraiser, dialogue-heavy, light tension.",
             "flags": {"violence": 0, "blood_gore": 0, "self_harm": 0, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 0, "sexual_content": 0, "bullying": 0, "substance_use": 1, "flash_seizure": 0, "loud_sensory": 0}},
            {"segment_id": 3, "start_time": "00:15:00", "end_time": "00:25:00",
             "summary": "Batman confronts criminals in a parking garage. Intense fight sequence.",
             "flags": {"violence": 4, "blood_gore": 1, "self_harm": 0, "suicide": 0, "gun_weapon": 2, "abuse": 0, "death_grief": 0, "sexual_content": 0, "bullying": 1, "substance_use": 0, "flash_seizure": 2, "loud_sensory": 3}},
            {"segment_id": 4, "start_time": "00:25:00", "end_time": "00:40:00",
             "summary": "Joker's threatening video message and interrogation scene. Psychological intimidation.",
             "flags": {"violence": 4, "blood_gore": 3, "self_harm": 0, "suicide": 0, "gun_weapon": 3, "abuse": 4, "death_grief": 3, "sexual_content": 0, "bullying": 3, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 3}},
            {"segment_id": 5, "start_time": "00:40:00", "end_time": "00:55:00",
             "summary": "Harvey Dent courthouse scene, chase sequence through the city, truck flipping.",
             "flags": {"violence": 4, "blood_gore": 1, "self_harm": 0, "suicide": 0, "gun_weapon": 4, "abuse": 0, "death_grief": 1, "sexual_content": 0, "bullying": 0, "substance_use": 0, "flash_seizure": 3, "loud_sensory": 5}},
        ],
        "plain_language_summary": "The Dark Knight contains intense action violence throughout, including gunfire, explosions, and hand-to-hand combat. The Joker's scenes involve psychological intimidation and threats. There are multiple character deaths. The film has loud, intense sequences with flashing lights during explosions and chase scenes. No sexual content or substance use. Recommended for older teens with co-viewing for intense sequences.",
    },
    {
        "title": "Inside Out 2",
        "year": 2024,
        "genre": ["Animation", "Family", "Comedy"],
        "runtime_minutes": 96,
        "poster_url": "https://image.tmdb.org/t/p/w500/vpnVM9B6NMmQpWeZvzLvDESb2QY.jpg",
        "synopsis": "Riley enters puberty and experiences a whole new set of emotions that turn her world upside down.",
        "mpaa_rating": "PG",
        "transcript_file": "inside_out_2.srt",
        "overall_flags": {
            "violence": "none", "blood_gore": "none", "self_harm": "mild",
            "suicide": "none", "gun_weapon": "none", "abuse": "none",
            "death_grief": "mild", "sexual_content": "none", "bullying": "moderate",
            "substance_use": "none", "flash_seizure": "none", "loud_sensory": "mild",
        },
        "segments": [
            {"segment_id": 1, "start_time": "00:00:00", "end_time": "00:10:00",
             "summary": "Riley's emotions are introduced. Lighthearted setup of her daily life.",
             "flags": {"violence": 0, "blood_gore": 0, "self_harm": 0, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 0, "sexual_content": 0, "bullying": 0, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 0}},
            {"segment_id": 2, "start_time": "00:10:00", "end_time": "00:25:00",
             "summary": "New emotions arrive — Anxiety takes control. Riley feels overwhelmed.",
             "flags": {"violence": 0, "blood_gore": 0, "self_harm": 1, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 0, "sexual_content": 0, "bullying": 1, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 2}},
            {"segment_id": 3, "start_time": "00:25:00", "end_time": "00:45:00",
             "summary": "Riley struggles with social dynamics at hockey camp. Conflicts with friends.",
             "flags": {"violence": 0, "blood_gore": 0, "self_harm": 2, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 1, "sexual_content": 0, "bullying": 3, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 1}},
            {"segment_id": 4, "start_time": "00:45:00", "end_time": "01:15:00",
             "summary": "Emotional climax — Riley has a panic attack. Emotions work together to help her.",
             "flags": {"violence": 0, "blood_gore": 0, "self_harm": 2, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 2, "sexual_content": 0, "bullying": 2, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 2}},
        ],
        "plain_language_summary": "Inside Out 2 explores anxiety, self-doubt, and growing up. No violence or explicit content, but contains emotionally intense scenes depicting panic attacks, social exclusion, and fear of not belonging. The bullying is social (exclusion, judgment) rather than physical.",
    },
    {
        "title": "Spider-Man: Across the Spider-Verse",
        "year": 2023,
        "genre": ["Animation", "Action", "Adventure"],
        "runtime_minutes": 140,
        "poster_url": "https://image.tmdb.org/t/p/w500/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg",
        "synopsis": "Miles Morales catapults across the Multiverse, where he encounters a team of Spider-People charged with protecting its very existence.",
        "mpaa_rating": "PG",
        "transcript_file": "spider_verse_2.srt",
        "overall_flags": {
            "violence": "moderate", "blood_gore": "mild", "self_harm": "none",
            "suicide": "none", "gun_weapon": "mild", "abuse": "none",
            "death_grief": "moderate", "sexual_content": "none", "bullying": "mild",
            "substance_use": "none", "flash_seizure": "intense", "loud_sensory": "intense",
        },
        "segments": [
            {"segment_id": 1, "start_time": "00:00:00", "end_time": "00:10:00",
             "summary": "Miles at home and school, establishing relationships.",
             "flags": {"violence": 0, "blood_gore": 0, "self_harm": 0, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 0, "sexual_content": 0, "bullying": 1, "substance_use": 0, "flash_seizure": 1, "loud_sensory": 1}},
            {"segment_id": 2, "start_time": "00:10:00", "end_time": "00:25:00",
             "summary": "First multiverse portal — fast visual cuts, bright flashing colors, intense action.",
             "flags": {"violence": 3, "blood_gore": 0, "self_harm": 0, "suicide": 0, "gun_weapon": 1, "abuse": 0, "death_grief": 0, "sexual_content": 0, "bullying": 0, "substance_use": 0, "flash_seizure": 5, "loud_sensory": 5}},
            {"segment_id": 3, "start_time": "00:25:00", "end_time": "00:50:00",
             "summary": "Miles meets the Spider-Society. Discussion of 'canon events' — tragedies that must happen.",
             "flags": {"violence": 2, "blood_gore": 1, "self_harm": 0, "suicide": 0, "gun_weapon": 1, "abuse": 0, "death_grief": 4, "sexual_content": 0, "bullying": 1, "substance_use": 0, "flash_seizure": 3, "loud_sensory": 3}},
            {"segment_id": 4, "start_time": "00:50:00", "end_time": "01:10:00",
             "summary": "Miles learns his father may die. Emotional confrontation and a massive chase.",
             "flags": {"violence": 3, "blood_gore": 1, "self_harm": 0, "suicide": 0, "gun_weapon": 2, "abuse": 0, "death_grief": 5, "sexual_content": 0, "bullying": 0, "substance_use": 0, "flash_seizure": 4, "loud_sensory": 4}},
        ],
        "plain_language_summary": "Spider-Man: Across the Spider-Verse features heavy visual stimulation with rapid scene changes and bright flashing portals. The flash/seizure risk is significant. The film deals with themes of parental death and loss. Action violence is stylized but frequent.",
    },
    {
        "title": "Wonder",
        "year": 2017,
        "genre": ["Drama", "Family"],
        "runtime_minutes": 113,
        "poster_url": "https://image.tmdb.org/t/p/w500/o0jEAezLV9TpFMGSXfMFMBpHTOR.jpg",
        "synopsis": "August Pullman, a boy with facial differences, enters fifth grade at a mainstream school for the first time.",
        "mpaa_rating": "PG",
        "transcript_file": "wonder.srt",
        "overall_flags": {
            "violence": "mild", "blood_gore": "none", "self_harm": "mild",
            "suicide": "none", "gun_weapon": "none", "abuse": "none",
            "death_grief": "moderate", "sexual_content": "none", "bullying": "intense",
            "substance_use": "none", "flash_seizure": "none", "loud_sensory": "mild",
        },
        "segments": [
            {"segment_id": 1, "start_time": "00:00:00", "end_time": "00:15:00",
             "summary": "Auggie's daily life at home. Nervous about starting school. Loving family.",
             "flags": {"violence": 0, "blood_gore": 0, "self_harm": 0, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 0, "sexual_content": 0, "bullying": 0, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 0}},
            {"segment_id": 2, "start_time": "00:15:00", "end_time": "00:35:00",
             "summary": "First days at school. Auggie faces staring, whispering, and overt bullying.",
             "flags": {"violence": 1, "blood_gore": 0, "self_harm": 1, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 0, "sexual_content": 0, "bullying": 5, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 1}},
            {"segment_id": 3, "start_time": "00:35:00", "end_time": "00:55:00",
             "summary": "Auggie makes a friend but discovers Jack was talking behind his back.",
             "flags": {"violence": 0, "blood_gore": 0, "self_harm": 2, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 1, "sexual_content": 0, "bullying": 4, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 0}},
            {"segment_id": 4, "start_time": "00:55:00", "end_time": "01:15:00",
             "summary": "Via's perspective — feeling invisible. Family dog Daisy dies.",
             "flags": {"violence": 0, "blood_gore": 0, "self_harm": 1, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 4, "sexual_content": 0, "bullying": 1, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 0}},
            {"segment_id": 5, "start_time": "01:15:00", "end_time": "01:50:00",
             "summary": "Physical confrontation on a field trip. Friends stand up for Auggie. Uplifting ending.",
             "flags": {"violence": 2, "blood_gore": 0, "self_harm": 0, "suicide": 0, "gun_weapon": 0, "abuse": 0, "death_grief": 0, "sexual_content": 0, "bullying": 3, "substance_use": 0, "flash_seizure": 0, "loud_sensory": 1}},
        ],
        "plain_language_summary": "Wonder is centered on bullying, acceptance, and kindness. The bullying ranges from social exclusion to a physical confrontation. A beloved pet dies on screen. Ultimately uplifting and promotes empathy.",
    },
]


def seed():
    now = datetime.now(timezone.utc).isoformat()

    # Clear existing movies
    supabase.table("movies").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print("Cleared existing movies.")

    for movie in SAMPLE_MOVIES:
        movie["analyzed_at"] = now

    result = supabase.table("movies").insert(SAMPLE_MOVIES).execute()
    print(f"Inserted {len(result.data)} sample movies.")
    for row in result.data:
        print(f"  {row['title']}: {row['id']}")


if __name__ == "__main__":
    seed()
