from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from config import settings
from db.session import engine
from routers import enroll, verify, logs, users

app = FastAPI(
    title       = "Lab Access Control System",
    description = "ArcFace-based facial recognition access control.",
    version     = "2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

app.include_router(enroll.router)
app.include_router(verify.router)
app.include_router(logs.router)
app.include_router(users.router)        


@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("[DB] Connection pool warmed up.")
    except Exception as e:
        print(f"[DB] Startup connection failed: {e}")


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Lab Access Control API v2.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.get("/debug", tags=["Health"])
async def debug_env():
    return {
        "threshold_allow": settings.threshold_allow,
        "threshold_deny":  settings.threshold_deny,
        "min_face_size":   settings.min_face_size,
    }