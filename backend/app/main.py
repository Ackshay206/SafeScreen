from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import profiles, movies, analysis

app = FastAPI(
    title="SafeScreen API",
    description="Privacy-safe personalized viewing plans for families",
    version="0.1.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(profiles.router)
app.include_router(movies.router)
app.include_router(analysis.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "safescreen"}
