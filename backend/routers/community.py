from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List

from backend.utils.db import get_db
from backend.models.models import ConsumerReport, CommunityVote, VoteType, Website
from backend.schemas.schemas import (
    VoteRequest,
    IndexItemResponse,
    WebsiteProfileResponse,
    ConsumerReportResponse,
)

router = APIRouter()


@router.post("/reports/{report_id}/vote")
async def vote_on_report(
    report_id: int, request: VoteRequest, db: Session = Depends(get_db)
):
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

    # Recalculate community score
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
async def get_index(limit: int = 20, db: Session = Depends(get_db)):
    websites = (
        db.query(Website)
        .order_by(desc(Website.report_count), desc(Website.risk_score))
        .limit(limit)
        .all()
    )

    result = []
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
                "community_confidence": 0.0,  # Could average report scores
                "major_patterns": [p[0] for p in major_patterns if p[0]],
                "first_reported": w.first_reported,
            }
        )
    return result


@router.get("/websites/{domain}", response_model=WebsiteProfileResponse)
async def get_website_profile(domain: str, db: Session = Depends(get_db)):
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
        "recent_reports": reports[:10],
        "last_analyzed": website.last_analyzed,
    }


@router.get("/search", response_model=List[IndexItemResponse])
async def search_websites(q: str, db: Session = Depends(get_db)):
    websites = db.query(Website).filter(Website.domain.ilike(f"%{q}%")).limit(10).all()
    result = []
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
