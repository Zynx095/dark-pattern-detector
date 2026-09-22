from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import List, Optional
from datetime import datetime
from backend.models.models import ReportStatus, VoteType


class FinancialImpactSchema(BaseModel):
    has_hidden_fee: bool = False
    estimated_amount: Optional[str] = None
    is_recurring: bool = False
    frequency: Optional[str] = None


class DetectedPatternSchema(BaseModel):
    type: str
    severity: str
    confidence: float
    evidence: str
    explanation: str
    financial_impact: FinancialImpactSchema = FinancialImpactSchema()


class AnalysisResultSchema(BaseModel):
    overall_risk_score: float
    risk_level: str
    patterns: List[DetectedPatternSchema]


class URLAnalysisRequest(BaseModel):
    url: str


class VoteRequest(BaseModel):
    vote: str


class ConsumerReportCreate(BaseModel):
    url: str
    description: str
    pattern_category: str
    severity: Optional[str] = "medium"
    evidence: Optional[str] = None
    analysis_id: Optional[int] = None


class ConsumerReportResponse(BaseModel):
    id: int
    website_id: int
    submitted_url: str
    description: str
    pattern_type: str
    severity: Optional[str] = "medium"
    evidence: Optional[str] = None
    screenshot_path: Optional[str] = None
    analysis_id: Optional[int] = None
    community_score: float = 0.0
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebsiteProfileResponse(BaseModel):
    domain: str
    risk_score: float
    risk_level: str
    total_reports: int
    confirmed_reports: int
    detected_patterns: List[str]
    recent_reports: List[ConsumerReportResponse]
    last_analyzed: Optional[datetime]


class IndexItemResponse(BaseModel):
    domain: str
    report_count: int
    risk_score: float
    risk_level: str
    community_confidence: float
    major_patterns: List[str]
    first_reported: datetime
