import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.utils.db import get_db
from backend.models.models import Base

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


MOCK_AI_RESULT = {
    "overall_risk_score": 85,
    "risk_level": "high",
    "patterns": [
        {
            "type": "hidden_recurring_fee",
            "severity": "high",
            "confidence": 0.95,
            "evidence": "Checkout displays ₹99 initial price; recurring ₹499/month charge appears in small grey text.",
            "explanation": "Users unknowingly sign up for an ongoing subscription.",
            "financial_impact": {
                "has_hidden_fee": True,
                "estimated_amount": "₹499",
                "is_recurring": True,
                "frequency": "monthly",
            },
        }
    ],
}

client = TestClient(app)


class TestAPI:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200

    @patch("backend.routers.analyze.analyze_with_gemini")
    @patch("backend.routers.analyze.scrape_website")
    def test_analyze_url(self, mock_scrape, mock_ai):
        mock_scrape.return_value = {"content": "test content", "error": None}
        mock_ai.return_value = MOCK_AI_RESULT

        response = client.post("/api/analyze/url", json={"url": "https://test.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["overall_risk_score"] == 85
        assert len(data["patterns"]) == 1
        pattern = data["patterns"][0]
        assert "financial_impact" in pattern
        assert pattern["financial_impact"]["has_hidden_fee"] is True
        assert pattern["financial_impact"]["estimated_amount"] == "₹499"
        assert pattern["financial_impact"]["is_recurring"] is True
        assert pattern["financial_impact"]["frequency"] == "monthly"

    def test_create_report(self):
        response = client.post(
            "/api/reports",
            json={
                "url": "https://test.com",
                "description": "Test report",
                "pattern_category": "hidden_fee",
                "severity": "high",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["submitted_url"] == "https://test.com"
        assert data["severity"] == "high"

    def test_community_vote(self):
        rep_resp = client.post(
            "/api/reports",
            json={
                "url": "https://test.com/subscribe",
                "description": "Hidden recurring subscription",
                "pattern_category": "hidden_recurring_fee",
                "severity": "high",
            },
        )
        assert rep_resp.status_code == 200
        report_id = rep_resp.json()["id"]

        vote_resp = client.post(
            f"/api/reports/{report_id}/vote", json={"vote": "confirm"}
        )
        assert vote_resp.status_code == 200
        data = vote_resp.json()
        assert data["confirm_count"] == 1
        assert data["community_confidence"] == 1.0
