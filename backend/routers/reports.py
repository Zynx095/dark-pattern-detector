from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import time

from backend.utils.db import get_db
from backend.services.scraper import extract_domain
from backend.models.models import ConsumerReport, Website, AnalysisResult, ReportStatus
from backend.schemas.schemas import ConsumerReportCreate, ConsumerReportResponse

router = APIRouter()


@router.post("", response_model=ConsumerReportResponse)
async def create_report(request: ConsumerReportCreate, db: Session = Depends(get_db)):
    domain = extract_domain(request.url)

    website = db.query(Website).filter(Website.domain == domain).first()
    if not website:
        website = Website(url=request.url, domain=domain)
        db.add(website)
        db.commit()
        db.refresh(website)

    website.report_count += 1

    report = ConsumerReport(
        website_id=website.id,
        submitted_url=request.url,
        description=request.description,
        pattern_type=request.pattern_category,
        severity=request.severity or "medium",
        evidence=request.evidence,
        analysis_id=request.analysis_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return report


@router.get("", response_model=List[ConsumerReportResponse])
async def list_reports(
    domain: Optional[str] = None,
    pattern_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(ConsumerReport)

    if domain:
        query = query.join(Website).filter(Website.domain.ilike(f"%{domain}%"))
    if pattern_type:
        query = query.filter(ConsumerReport.pattern_type == pattern_type)

    reports = (
        query.order_by(desc(ConsumerReport.created_at)).offset(skip).limit(limit).all()
    )
    return reports


@router.get("/{report_id}", response_model=ConsumerReportResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ConsumerReport).filter(ConsumerReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
