from pathlib import Path
import os
from dotenv import load_dotenv

# Explicit .env resolution: load from backend directory as well as repository root
backend_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=backend_env_path)
root_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=root_env_path)
load_dotenv()  # Fallback to current working directory

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.routers import analyze, reports, community
from backend.utils.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        print(f"[AI ENGINE] GEMINI_API_KEY found (starts with: {gemini_key[:6]}...).")
    else:
        print("[AI ENGINE] WARNING: GEMINI_API_KEY not found in environment.")
    yield


app = FastAPI(
    title="Cyber-Safety Dark Pattern & Hidden Fee Detector",
    description="A consumer reporting portal for identifying and sharing deceptive e-commerce practices.",
    version="2.0.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    return response


app.include_router(analyze.router, prefix="/api/analyze", tags=["Analysis"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(community.router, prefix="/api", tags=["Community"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": "2.0.0"}
