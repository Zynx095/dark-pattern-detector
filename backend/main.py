"""Main FastAPI Application Entry Point.

Configures CORS, Security Headers, GZip Compression, and API Routers.
"""

from pathlib import Path
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

# Explicit .env resolution: load from backend directory as well as repository root
backend_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=backend_env_path)
root_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=root_env_path)
load_dotenv()  # Fallback to current working directory

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from backend.routers import analyze, reports, community
from backend.utils.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager to initialize DB and verify AI API configuration."""
    init_db()

    free_key = os.getenv("FREE_LLM_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if free_key or openai_key:
        provider_url = os.getenv("FREE_LLM_BASE_URL", "https://api.openai.com/v1")
        model_name = os.getenv("FREE_LLM_MODEL", "gpt-4o-mini")
        print(
            f"[AI ENGINE] Active Provider: OpenAI-compatible ({provider_url}) | Model: {model_name}"
        )
    elif gemini_key:
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        print(f"[AI ENGINE] Active Provider: Google Gemini API | Model: {model_name}")
    else:
        print(
            "[AI ENGINE] WARNING: No LLM API key detected. System will default to mock mode."
        )

    yield


app = FastAPI(
    title="Cyber-Safety Dark Pattern & Hidden Fee Detector",
    description="A consumer reporting portal for identifying and sharing deceptive e-commerce practices.",
    version="2.0.0",
    lifespan=lifespan,
)

# Compression Middleware for maximum response efficiency
app.add_middleware(GZipMiddleware, minimum_size=1000)

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
async def add_security_headers(request: Request, call_next: any) -> Response:
    """HTTP middleware to attach standard security headers to all responses."""
    response: Response = await call_next(request)
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
async def health() -> dict[str, str]:
    """Health check endpoint confirming API status."""
    return {"status": "healthy", "version": "2.0.0"}
