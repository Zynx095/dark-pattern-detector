import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.models import (
    Base,
    Website,
    ConsumerReport,
    AnalysisResult,
    DetectedPattern,
    CommunityVote,
    ReportStatus,
    VoteType,
)
from datetime import datetime, timedelta
import random

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./darkpattern.db")

# Render PostgreSQL URLs start with postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("[INFO] Seeding database with realistic consumer reports...")

        # Site 1
        w1 = Website(
            url="https://example-shop.com",
            domain="example-shop.com",
            risk_level="high",
            risk_score=85.0,
            report_count=1,
        )
        db.add(w1)
        db.commit()

        a1 = AnalysisResult(
            website_id=w1.id,
            source_type="url",
            overall_risk_score=85.0,
            patterns_detected=1,
            explanation="Detected a hidden subscription fee.",
        )
        db.add(a1)
        db.commit()

        p1 = DetectedPattern(
            analysis_id=a1.id,
            pattern_type="hidden_recurring_fee",
            severity="high",
            confidence=0.95,
            evidence="Headline displays ₹99 trial price; footnote reveals recurring charge of ₹499/month.",
            explanation="User is signed up for a subscription without clear consent.",
            has_hidden_fee=True,
            estimated_amount="₹499",
            is_recurring=True,
            frequency="monthly",
        )
        db.add(p1)

        r1 = ConsumerReport(
            website_id=w1.id,
            submitted_url="https://example-shop.com/checkout",
            description="They charged me ₹499 a month after I bought a ₹99 trial item!",
            pattern_type="hidden_recurring_fee",
            severity="high",
            evidence="Checkout screenshot only emphasized ₹99.",
            analysis_id=a1.id,
            status=ReportStatus.VERIFIED,
        )
        db.add(r1)
        db.commit()

        v1 = CommunityVote(report_id=r1.id, vote_type=VoteType.CONFIRM)
        v2 = CommunityVote(report_id=r1.id, vote_type=VoteType.CONFIRM)
        db.add_all([v1, v2])

        r1.community_score = 1.0  # 2 confirms, 0 disputes

        # Site 2
        w2 = Website(
            url="https://sneaky-travel.com",
            domain="sneaky-travel.com",
            risk_level="medium",
            risk_score=60.0,
            report_count=1,
        )
        db.add(w2)
        db.commit()

        a2 = AnalysisResult(
            website_id=w2.id,
            source_type="url",
            overall_risk_score=60.0,
            patterns_detected=1,
            explanation="Detected pre-selected travel insurance.",
        )
        db.add(a2)
        db.commit()

        p2 = DetectedPattern(
            analysis_id=a2.id,
            pattern_type="preselection",
            severity="medium",
            confidence=0.88,
            evidence="Insurance checkbox of ₹350 is ticked by default.",
            explanation="Users might pay for insurance they don't want.",
            has_hidden_fee=True,
            estimated_amount="₹350",
            is_recurring=False,
            frequency="one-time",
        )
        db.add(p2)

        r2 = ConsumerReport(
            website_id=w2.id,
            submitted_url="https://sneaky-travel.com/book",
            description="Insurance was added automatically to my flight.",
            pattern_type="preselection",
            severity="medium",
            evidence="Checkbox is checked by default.",
            analysis_id=a2.id,
            status=ReportStatus.PENDING,
        )
        db.add(r2)
        db.commit()

        v3 = CommunityVote(report_id=r2.id, vote_type=VoteType.CONFIRM)
        v4 = CommunityVote(report_id=r2.id, vote_type=VoteType.DISPUTE)
        db.add_all([v3, v4])

        r2.community_score = 0.5  # 1 confirm, 1 dispute

        db.commit()
        print("[SUCCESS] Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
