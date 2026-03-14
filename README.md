# 🛡️ SafeScreen

A privacy-safe parental media tool that generates personalized viewing plans for emotionally intense movies, so children can watch media more safely based on their sensitivities and the content of the film.

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend | React (Vite) |
| Backend | FastAPI (Python) |
| Database | Supabase (PostgreSQL) |
| LLM | OpenAI GPT-4o (planned) |

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your Supabase and OpenAI credentials:

```bash
cp .env.example .env
```

Create the database tables by pasting `schema.sql` into the Supabase SQL Editor, then seed sample movies:

```bash
python -m app.seed
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## Features

- **Child Profiles** — Create profiles with 12 sensitivity sliders and a custom calming strategy
- **Movie Dashboard** — Browse movies with color-coded content flag badges
- **Movie Detail** — View overall safety summary, content flags, and a scene-by-scene intensity timeline
- **Viewing Plans** — *(coming soon)* Personalized skip/blur/co-view/pace plans based on child profile × movie analysis
- **Post-Watch Feedback** — *(coming soon)* Lightweight feedback to improve follow-up recommendations

## Content Flags (12)

Violence · Blood/Gore · Self-Harm · Suicide · Gun/Weapon · Abuse · Death/Grief · Sexual Content · Bullying · Substance Use · Flash/Seizure · Loud/Sensory