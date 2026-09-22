"""FastAPI Router for Consumer Deceptive Pattern Reporting Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.utils.db import get_db
from backend.services.scraper import extract_domain
from backend.models.models import ConsumerReport, Website
from backend.schemas.schemas import ConsumerReportCreate, ConsumerReportResponse

router = APIRouter()


@router.post("", response_model=ConsumerReportResponse)
async def create_report(
    request: ConsumerReportCreate, db: Session = Depends(get_db)
) -> ConsumerReport:
    """Submits a new consumer report for an unethical website layout or deceptive fee.

    Args:
        request: ConsumerReportCreate schema.
        db: Database session dependency.

    Returns:
        Created ConsumerReport database entity.
    """
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
) -> List[ConsumerReport]:
    """Lists submitted consumer reports with optional filtering by domain or pattern category.

    Args:
        domain: Filter reports by domain substring.
        pattern_type: Filter reports by pattern category.
        skip: Pagination offset.
        limit: Max items to return.
        db: Database session dependency.

    Returns:
        List of ConsumerReport database entities.
    """
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
async def get_report(report_id: int, db: Session = Depends(get_db)) -> ConsumerReport:
    """Retrieves a single consumer report by its unique ID.

    Args:
        report_id: Report entity primary key.
        db: Database session dependency.

    Returns:
        ConsumerReport model entity.
    """
    report = db.query(ConsumerReport).filter(ConsumerReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
