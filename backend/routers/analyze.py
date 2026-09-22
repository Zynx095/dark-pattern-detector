"""FastAPI Router for URL and Screenshot Dark Pattern Analysis Endpoints."""

import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.utils.db import get_db
from backend.services.scraper import scrape_website, extract_domain
from backend.services.ai_analyzer import (
    analyze_with_gemini,
    analyze_screenshot_with_gemini,
)
from backend.models.models import AnalysisResult, DetectedPattern, Website
from backend.schemas.schemas import URLAnalysisRequest, AnalysisResultSchema

router = APIRouter()


def save_analysis(
    db: Session, ai_result: Dict[str, Any], url: Optional[str] = None
) -> AnalysisResult:
    """Persists analysis result and detected patterns into database.

    Args:
        db: Active SQLAlchemy database session.
        ai_result: Parsed dictionary returned from AI analyzer service.
        url: Optional target website URL.

    Returns:
        Created AnalysisResult model entity.
    """
    domain = extract_domain(url) if url else "screenshot-upload"

    website = db.query(Website).filter(Website.domain == domain).first()
    if not website:
        website = Website(url=url or "screenshot", domain=domain)
        db.add(website)
        db.commit()
        db.refresh(website)

    website.last_analyzed = datetime.now(timezone.utc)
    website.risk_score = float(ai_result.get("overall_risk_score", 0.0))
    website.risk_level = str(ai_result.get("risk_level", "low"))
    db.commit()

    patterns = ai_result.get("patterns", [])

    analysis = AnalysisResult(
        website_id=website.id,
        source_type="url" if url else "screenshot",
        overall_risk_score=float(ai_result.get("overall_risk_score", 0.0)),
        patterns_detected=len(patterns),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    for p in patterns:
        fi = p.get("financial_impact") or {}
        pattern = DetectedPattern(
            analysis_id=analysis.id,
            pattern_type=str(p.get("type", "unknown")),
            severity=str(p.get("severity", "low")),
            confidence=float(p.get("confidence", 0.0)),
            evidence=str(p.get("evidence", "")),
            explanation=str(p.get("explanation", "")),
            has_hidden_fee=bool(fi.get("has_hidden_fee", False)),
            estimated_amount=fi.get("estimated_amount"),
            is_recurring=bool(fi.get("is_recurring", False)),
            frequency=fi.get("frequency"),
        )
        db.add(pattern)

    db.commit()
    return analysis


@router.post("/url", response_model=AnalysisResultSchema)
async def analyze_url(
    request: URLAnalysisRequest, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Analyzes a web page URL for deceptive dark patterns and hidden recurring fees.

    Args:
        request: Pydantic request schema containing target URL.
        db: Database session dependency.

    Returns:
        AnalysisResultSchema response detailing detected patterns and financial impact.
    """
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
) -> Dict[str, Any]:
    """Uploads and analyzes an e-commerce page screenshot image for visual dark patterns.

    Args:
        file: Form-data image file upload.
        db: Database session dependency.

    Returns:
        AnalysisResultSchema detailing visual dark patterns detected.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    os.makedirs("backend/uploads", exist_ok=True)
    ext = (
        file.filename.split(".")[-1]
        if file.filename and "." in file.filename
        else "png"
    )
    file_path = f"backend/uploads/{uuid.uuid4()}.{ext}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ai_result = await analyze_screenshot_with_gemini(file_path)
    save_analysis(db, ai_result)

    return ai_result
