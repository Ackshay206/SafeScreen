from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import profiles, movies, analysis, recommendations, viewing_plan, profile_chat
from app.routers.feedback import router as feedback_router

app = FastAPI(title="SafeScreen API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(movies.router)
app.include_router(analysis.router)
app.include_router(recommendations.router)
app.include_router(viewing_plan.router)
app.include_router(profile_chat.router)
app.include_router(feedback_router)


@app.get("/")
async def root():
    return {"message": "SafeScreen API is running"}