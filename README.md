# 🛡️ SafeScreen

**Intelligent & Adaptive Media Safety for Families**

SafeScreen is an AI-powered media safety platform that goes beyond generic age ratings (like PG-13 or R). We recognize that every viewer has unique emotional and psychological sensitivities. By building custom sensitivity profiles and using advanced Large Language Models (LLMs) to analyze movie transcripts scene-by-scene, SafeScreen proactively generates personalized, holistic viewing plans.

Instead of just reacting to triggers or arbitrarily blocking content, SafeScreen empowers families to navigate intense scenes thoughtfully through co-viewing recommendations, dynamic scene-skipping (blurring/muting), planned intermissions, and personalized post-watch decompression strategies.

---

## 🌟 Key Features

1. **Adaptive Profile Questionnaire:** 
   A conversational AI agent (powered by Gemini) deduces the nuanced sensitivities of a child or viewer (e.g., "Are they okay with cartoon violence vs. realistic combat?") to build a comprehensive psychological profile.
2. **Scene-by-Scene Analysis:** 
   Using Gemini to parse raw SRT transcripts, the backend identifies distinct narrative scenes, generating exact timestamps and assigning specific content flags (Violence, Bullying, Grief, Self-Harm, etc.).
3. **Personalized Viewing Plans:** 
   By cross-referencing a movie's flagged scenes against a viewer's personal sensitivity profile, SafeScreen generates a concrete action plan for every scene (Watch, Skip, Mute, Blur, or Co-View).
4. **Session Pacing & Parent Prompts:** 
   Automatically suggests optimal pause checkpoints for intense movies, and surfaces contextual prompts for parents to guide healthy discussions.
5. **Post-Watch Decompression:** 
   If a viewer reports distress after watching, SafeScreen dynamically generates a curated list of calming YouTube resources (e.g., box breathing exercises, cute animal videos) based on their predefined calming strategies.

---

## 🏗️ Architecture & Tech Stack

SafeScreen is built using a modern, scalable, AI-first architecture:

### Frontend
* **Framework:** React + Vite
* **Styling:** Custom CSS (Modern, accessible, responsive design)
* **API Communication:** Axios via customized API Client
* **Routing:** React Router DOM

### Backend
* **Framework:** FastAPI (Python)
* **AI Integration:** Google Gemini (gemini-2.5-pro for analysis and profile generation, gemini-2.5-flash for rapid feedback generation)
* **Transcript Parsing:** Custom autonomous SRT processing pipeline

### Database
* **Database:** Supabase (PostgreSQL)
* **Deployment & Storage:** Secure profile and pre-analyzed metadata storage, caching LLM responses to ensure lightning-fast UI load times.

---

## 🚀 Getting Started (Local Development)

### Prerequisites
* **Node.js** (v18+ recommended)
* **Python** (v3.10+ recommended)
* **Supabase Account** (for database)
* **Google Gemini API Key**

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/SafeScreen.git
cd SafeScreen
```

### 2. Backend Setup
```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Edit .env and add your SUPABASE_URL, SUPABASE_KEY, and GEMINI_API_KEY
```

To run the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```
*The API will be available at `http://localhost:8000`. You can view Swagger documentation at `http://localhost:8000/docs`.*

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
*The frontend will be available at `http://localhost:5173`.*

### 4. Seeding the Database (Optional)
If you have local transcript files (`.srt`) in the `backend/transcripts/` directory, you can run the seed script to populate the database with movies, chunk the transcripts, and run them through the Gemini analysis pipeline.
```bash
cd backend
source venv/bin/activate
export PYTHONPATH="."
python -m app.seed
```

---

## 🧠 Future Roadmap

Our ultimate goal is to evolve SafeScreen into a zero-touch browser extension. By hooking directly into streaming platforms (Netflix, Disney+, etc.) and intercepting the video player, SafeScreen will automatically execute the generated viewing plan—muting the audio, applying CSS blur overlays, or pausing the video at the exact AI-generated timestamps.

---

## 🤝 Contributing
Built during a Hackathon! Feedback and contributions to push media safety forward are always welcome.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

*Because everyone deserves to watch safely.*