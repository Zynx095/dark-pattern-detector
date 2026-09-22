from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import time
import os
import shutil
import uuid

from backend.utils.db import get_db
from backend.services.scraper import scrape_website, extract_domain
from backend.services.ai_analyzer import (
    analyze_with_gemini,
    analyze_screenshot_with_gemini,
)
from backend.models.models import AnalysisResult, DetectedPattern, Website
from backend.schemas.schemas import URLAnalysisRequest, AnalysisResultSchema

router = APIRouter()

from datetime import datetime, timezone


def save_analysis(db: Session, ai_result: dict, url: str = None) -> AnalysisResult:
    domain = extract_domain(url) if url else "screenshot-upload"

    # Upsert website
    website = db.query(Website).filter(Website.domain == domain).first()
    if not website:
        website = Website(url=url or "screenshot", domain=domain)
        db.add(website)
        db.commit()
        db.refresh(website)

    website.last_analyzed = datetime.now(timezone.utc)
    website.risk_score = ai_result.get("overall_risk_score", 0.0)
    website.risk_level = ai_result.get("risk_level", "low")
    db.commit()

    patterns = ai_result.get("patterns", [])

    analysis = AnalysisResult(
        website_id=website.id,
        source_type="url" if url else "screenshot",
        overall_risk_score=ai_result.get("overall_risk_score", 0.0),
        patterns_detected=len(patterns),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    for p in patterns:
        fi = p.get("financial_impact") or {}
        pattern = DetectedPattern(
            analysis_id=analysis.id,
            pattern_type=p.get("type", "unknown"),
            severity=p.get("severity", "low"),
            confidence=p.get("confidence", 0.0),
            evidence=p.get("evidence", ""),
            explanation=p.get("explanation", ""),
            has_hidden_fee=bool(fi.get("has_hidden_fee", False)),
            estimated_amount=fi.get("estimated_amount"),
            is_recurring=bool(fi.get("is_recurring", False)),
            frequency=fi.get("frequency"),
        )
        db.add(pattern)

    db.commit()
    return ai_result


@router.post("/url", response_model=AnalysisResultSchema)
async def analyze_url(request: URLAnalysisRequest, db: Session = Depends(get_db)):
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    scraped = await scrape_website(url)
    if scraped.get("error") and not scraped.get("content"):
        raise HTTPException(
            status_code=400, detail=f"Could not access website: {scraped['error']}"
        )

    ai_result = await analyze_with_gemini(scraped.get("content", ""), url)
    save_analysis(db, ai_result, url)
    return ai_result


@router.post("/screenshot", response_model=AnalysisResultSchema)
async def analyze_screenshot(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    os.makedirs("backend/uploads", exist_ok=True)
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    file_path = f"backend/uploads/{uuid.uuid4()}.{ext}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ai_result = await analyze_screenshot_with_gemini(file_path)
    save_analysis(db, ai_result)

    return ai_result
