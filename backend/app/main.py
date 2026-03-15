from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import profiles, movies, analysis, recommendations, viewing_plan

app = FastAPI(
    title="SafeScreen API",
    description="Privacy-safe personalized viewing plans for families",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(movies.router)
app.include_router(analysis.router)
app.include_router(recommendations.router)
app.include_router(viewing_plan.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "safescreen"}