from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
from typing import Any
import enum

Base = declarative_base()


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    RESOLVED = "resolved"


class VoteType(str, enum.Enum):
    CONFIRM = "confirm"
    DISPUTE = "dispute"


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    domain = Column(String(200), index=True)
    risk_level = Column(String(50), default="low")
    risk_score = Column(Float, default=0.0)
    first_reported = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_analyzed = Column(DateTime, nullable=True)
    report_count = Column(Integer, default=0)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    reports = relationship(
        "ConsumerReport", back_populates="website", cascade="all, delete-orphan"
    )
    analyses = relationship(
        "AnalysisResult", back_populates="website", cascade="all, delete-orphan"
    )


class ConsumerReport(Base):
    __tablename__ = "consumer_reports"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    submitted_url = Column(String(500), nullable=False)
    description = Column(Text)
    pattern_type = Column(String(100))
    severity = Column(String(50))
    evidence = Column(Text)
    screenshot_path = Column(String(500), nullable=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=True)
    community_score = Column(Float, default=0.0)
    status = Column(String(50), default=ReportStatus.PENDING)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    website = relationship("Website", back_populates="reports")
    analysis = relationship("AnalysisResult")
    votes = relationship(
        "CommunityVote", back_populates="report", cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    source_type = Column(String(50), default="url")  # 'url' or 'screenshot'
    overall_risk_score = Column(Float, default=0.0)
    patterns_detected = Column(Integer, default=0)
    explanation = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    website = relationship("Website", back_populates="analyses")
    patterns = relationship(
        "DetectedPattern", back_populates="analysis", cascade="all, delete-orphan"
    )


class DetectedPattern(Base):
    __tablename__ = "detected_patterns"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    pattern_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    confidence = Column(Float, default=0.0)
    evidence = Column(Text)
    explanation = Column(Text)
    has_hidden_fee = Column(Boolean, default=False)
    estimated_amount = Column(String(50), nullable=True)
    is_recurring = Column(Boolean, default=False)
    frequency = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = relationship("AnalysisResult", back_populates="patterns")

    @property
    def financial_impact(self) -> dict[str, Any]:
        """Returns structured dictionary representation of pattern's financial impact."""
        return {
            "has_hidden_fee": bool(self.has_hidden_fee),
            "estimated_amount": self.estimated_amount,
            "is_recurring": bool(self.is_recurring),
            "frequency": self.frequency,
        }


class CommunityVote(Base):
    __tablename__ = "community_votes"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("consumer_reports.id"), nullable=False)
    vote_type = Column(String(50), nullable=False)  # 'confirm' or 'dispute'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    report = relationship("ConsumerReport", back_populates="votes")
