"""FastAPI Router for Community Voting, Website Index, and Search Endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.utils.db import get_db
from backend.models.models import ConsumerReport, CommunityVote, VoteType, Website
from backend.schemas.schemas import (
    VoteRequest,
    IndexItemResponse,
    WebsiteProfileResponse,
)

router = APIRouter()


@router.post("/reports/{report_id}/vote")
async def vote_on_report(
    report_id: int, request: VoteRequest, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Records a community confirmation or dispute vote for a consumer report.

    Args:
        report_id: Target consumer report ID.
        request: VoteRequest containing vote value ('confirm' or 'dispute').
        db: Database session dependency.

    Returns:
        Dict with updated vote counts and confidence score.
    """
    if request.vote not in [VoteType.CONFIRM, VoteType.DISPUTE]:
        raise HTTPException(
            status_code=400, detail="Vote must be 'confirm' or 'dispute'"
        )

    report = db.query(ConsumerReport).filter(ConsumerReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    vote = CommunityVote(report_id=report_id, vote_type=request.vote)
    db.add(vote)
    db.commit()

    confirms = (
        db.query(func.count(CommunityVote.id))
        .filter(
            CommunityVote.report_id == report_id,
            CommunityVote.vote_type == VoteType.CONFIRM,
        )
        .scalar()
        or 0
    )
    disputes = (
        db.query(func.count(CommunityVote.id))
        .filter(
            CommunityVote.report_id == report_id,
            CommunityVote.vote_type == VoteType.DISPUTE,
        )
        .scalar()
        or 0
    )

    total = confirms + disputes
    report.community_score = (confirms / total) if total > 0 else 0.0
    db.commit()

    return {
        "message": "Vote recorded",
        "confirm_count": confirms,
        "dispute_count": disputes,
        "community_confidence": report.community_score,
    }


@router.get("/index", response_model=List[IndexItemResponse])
async def get_index(
    limit: int = 20, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Retrieves community-voted index of unethical web layouts sorted by report count and risk.

    Args:
        limit: Number of items to return.
        db: Database session dependency.

    Returns:
        List of IndexItemResponse objects.
    """
    websites = (
        db.query(Website)
        .order_by(desc(Website.report_count), desc(Website.risk_score))
        .limit(limit)
        .all()
    )

    result: List[Dict[str, Any]] = []
    for w in websites:
        major_patterns = (
            db.query(ConsumerReport.pattern_type)
            .filter(ConsumerReport.website_id == w.id)
            .distinct()
            .all()
        )
        result.append(
            {
                "domain": w.domain,
                "report_count": w.report_count,
                "risk_score": w.risk_score,
                "risk_level": w.risk_level,
                "community_confidence": 0.0,
                "major_patterns": [p[0] for p in major_patterns if p[0]],
                "first_reported": w.first_reported,
            }
        )
    return result


@router.get("/websites/{domain}", response_model=WebsiteProfileResponse)
async def get_website_profile(
    domain: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retrieves aggregate cyber-safety profile and recent reports for a target domain.

    Args:
        domain: Domain name string.
        db: Database session dependency.

    Returns:
        WebsiteProfileResponse containing total reports, patterns, and recent reports list.
    """
    website = db.query(Website).filter(Website.domain == domain).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    reports = (
        db.query(ConsumerReport)
        .filter(ConsumerReport.website_id == website.id)
        .order_by(desc(ConsumerReport.created_at))
        .all()
    )
    patterns = list(set([r.pattern_type for r in reports if r.pattern_type]))

    return {
        "domain": website.domain,
        "risk_score": website.risk_score,
        "risk_level": website.risk_level,
        "total_reports": len(reports),
        "confirmed_reports": len([r for r in reports if r.community_score > 0.5]),
        "detected_patterns": patterns,
        "recent_reports": reports,
        "last_analyzed": website.last_analyzed,
    }


@router.get("/search", response_model=List[IndexItemResponse])
async def search_websites(
    q: str, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Searches indexed websites by domain query string.

    Args:
        q: Search query substring.
        db: Database session dependency.

    Returns:
        List of matching IndexItemResponse objects.
    """
    websites = db.query(Website).filter(Website.domain.ilike(f"%{q}%")).limit(10).all()
    result: List[Dict[str, Any]] = []
    for w in websites:
        major_patterns = (
            db.query(ConsumerReport.pattern_type)
            .filter(ConsumerReport.website_id == w.id)
            .distinct()
            .all()
        )
        result.append(
            {
                "domain": w.domain,
                "report_count": w.report_count,
                "risk_score": w.risk_score,
                "risk_level": w.risk_level,
                "community_confidence": 0.0,
                "major_patterns": [p[0] for p in major_patterns if p[0]],
                "first_reported": w.first_reported,
            }
        )
    return result
