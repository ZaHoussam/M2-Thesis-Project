# ================================================================
#  main.py — FastAPI application entry point
# ================================================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import enroll, verify

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


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Lab Access Control API v2.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.get("/debug-env", tags=["Health"])
async def debug_env():
    return {
        "threshold_allow":         settings.threshold_allow,
        "max_embeddings_per_user": settings.max_embeddings_per_user,
        "min_face_size":           settings.min_face_size,
    }