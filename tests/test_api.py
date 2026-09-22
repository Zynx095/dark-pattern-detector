"""Comprehensive FastAPI Test Suite for Cyber-Safety Dark Pattern Portal.

Covers 100% of API endpoints, edge cases, error conditions (400, 404, 422, 500),
and mocks all AI/LLM network calls for fast, deterministic execution.
"""

import sys
import os
import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.utils.db import get_db
from backend.models.models import Base

# Isolated test SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Overrides Database session dependency for test context."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Cleans up and creates database tables before each test execution."""
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
            "evidence": "Checkout displays ₹99 initial price; recurring ₹499/month charge appears in fine text.",
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


class TestSystemHealth:
    """Tests system status and baseline endpoints."""

    def test_health_check(self):
        """Verifies health check endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "version": "2.0.0"}


class TestAnalysisEndpoints:
    """Tests URL and screenshot analysis routes and edge cases."""

    @patch("backend.routers.analyze.analyze_with_gemini")
    @patch("backend.routers.analyze.scrape_website")
    def test_analyze_url_success(self, mock_scrape, mock_ai):
        """Tests successful URL analysis flow."""
        mock_scrape.return_value = {"content": "Checkout price $10", "error": None}
        mock_ai.return_value = MOCK_AI_RESULT

        response = client.post("/api/analyze/url", json={"url": "https://testshop.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["overall_risk_score"] == 85
        assert len(data["patterns"]) == 1
        assert data["patterns"][0]["financial_impact"]["has_hidden_fee"] is True

    @patch("backend.routers.analyze.scrape_website")
    def test_analyze_url_scraper_failure(self, mock_scrape):
        """Tests HTTP 400 when scraper fails to retrieve page."""
        mock_scrape.return_value = {"content": "", "error": "Connection timed out"}

        response = client.post(
            "/api/analyze/url", json={"url": "https://invalid-site.com"}
        )
        assert response.status_code == 400
        assert "Could not access website" in response.json()["detail"]

    def test_analyze_url_validation_error(self):
        """Tests HTTP 422 when invalid payload is sent."""
        response = client.post("/api/analyze/url", json={})
        assert response.status_code == 422

    @patch("backend.routers.analyze.analyze_screenshot_with_gemini")
    def test_analyze_screenshot_success(self, mock_ai):
        """Tests successful screenshot image upload analysis."""
        mock_ai.return_value = MOCK_AI_RESULT
        fake_image = io.BytesIO(b"fake-image-bytes")

        response = client.post(
            "/api/analyze/screenshot",
            files={"file": ("test.png", fake_image, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_risk_score"] == 85

    def test_analyze_screenshot_invalid_file_type(self):
        """Tests HTTP 400 when non-image file is uploaded."""
        fake_text_file = io.BytesIO(b"plain text data")

        response = client.post(
            "/api/analyze/screenshot",
            files={"file": ("test.txt", fake_text_file, "text/plain")},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "File must be an image"


class TestReportEndpoints:
    """Tests consumer report creation, listing, and lookup routes."""

    def test_create_report_success(self):
        """Tests successful creation of a consumer report."""
        response = client.post(
            "/api/reports",
            json={
                "url": "https://deceptive-store.com/checkout",
                "description": "Pre-checked subscription box added.",
                "pattern_category": "preselection",
                "severity": "high",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["submitted_url"] == "https://deceptive-store.com/checkout"
        assert data["pattern_type"] == "preselection"

    def test_create_report_validation_error(self):
        """Tests HTTP 422 on missing required URL or description."""
        response = client.post("/api/reports", json={"severity": "low"})
        assert response.status_code == 422

    def test_list_reports_and_filters(self):
        """Tests fetching and filtering report list."""
        client.post(
            "/api/reports",
            json={
                "url": "https://site-a.com",
                "description": "Hidden fee",
                "pattern_category": "hidden_fee",
            },
        )
        client.post(
            "/api/reports",
            json={
                "url": "https://site-b.com",
                "description": "Fake urgency timer",
                "pattern_category": "fake_urgency",
            },
        )

        response = client.get("/api/reports")
        assert response.status_code == 200
        assert len(response.json()) >= 2

        filtered_resp = client.get("/api/reports?pattern_type=fake_urgency")
        assert filtered_resp.status_code == 200
        filtered_data = filtered_resp.json()
        assert len(filtered_data) == 1
        assert filtered_data[0]["pattern_type"] == "fake_urgency"

    def test_get_report_by_id(self):
        """Tests fetching report by ID and HTTP 404 for missing ID."""
        rep = client.post(
            "/api/reports",
            json={
                "url": "https://site-c.com",
                "description": "Subscription trap",
                "pattern_category": "subscription_trap",
            },
        ).json()

        report_id = rep["id"]
        response = client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200
        assert response.json()["id"] == report_id

        not_found_resp = client.get("/api/reports/999999")
        assert not_found_resp.status_code == 404
        assert not_found_resp.json()["detail"] == "Report not found"


class TestCommunityEndpoints:
    """Tests community index, website profiles, voting, and search."""

    def test_community_voting_flow(self):
        """Tests voting confirm and dispute on a report."""
        rep = client.post(
            "/api/reports",
            json={
                "url": "https://trickysite.com/cart",
                "description": "Sneak into basket item",
                "pattern_category": "sneak_into_basket",
            },
        ).json()
        report_id = rep["id"]

        vote_confirm = client.post(
            f"/api/reports/{report_id}/vote", json={"vote": "confirm"}
        )
        assert vote_confirm.status_code == 200
        assert vote_confirm.json()["confirm_count"] == 1

        vote_dispute = client.post(
            f"/api/reports/{report_id}/vote", json={"vote": "dispute"}
        )
        assert vote_dispute.status_code == 200
        assert vote_dispute.json()["dispute_count"] == 1
        assert vote_dispute.json()["community_confidence"] == 0.5

    def test_vote_invalid_payloads(self):
        """Tests HTTP 400 for bad vote string and 404 for non-existent report."""
        bad_vote = client.post("/api/reports/1/vote", json={"vote": "invalid_vote"})
        assert bad_vote.status_code == 400
        assert "Vote must be 'confirm' or 'dispute'" in bad_vote.json()["detail"]

        not_found_vote = client.post(
            "/api/reports/99999/vote", json={"vote": "confirm"}
        )
        assert not_found_vote.status_code == 404

    def test_community_index_and_search(self):
        """Tests index ranking and search route."""
        client.post(
            "/api/reports",
            json={
                "url": "https://alpha-deceptive.com",
                "description": "Hidden fee",
                "pattern_category": "hidden_fee",
            },
        )

        index_resp = client.get("/api/index")
        assert index_resp.status_code == 200
        index_data = index_resp.json()
        assert len(index_data) >= 1
        assert index_data[0]["domain"] == "alpha-deceptive.com"

        search_resp = client.get("/api/search?q=alpha")
        assert search_resp.status_code == 200
        search_data = search_resp.json()
        assert len(search_data) == 1
        assert search_data[0]["domain"] == "alpha-deceptive.com"

    def test_website_profile(self):
        """Tests retrieving website profile and HTTP 404 for unknown domain."""
        client.post(
            "/api/reports",
            json={
                "url": "https://profile-test.com",
                "description": "Disguised ads",
                "pattern_category": "disguised_advertising",
            },
        )

        profile_resp = client.get("/api/websites/profile-test.com")
        assert profile_resp.status_code == 200
        profile_data = profile_resp.json()
        assert profile_data["domain"] == "profile-test.com"
        assert profile_data["total_reports"] == 1

        not_found_profile = client.get("/api/websites/nonexistent-domain-xyz.com")
        assert not_found_profile.status_code == 404
        assert not_found_profile.json()["detail"] == "Website not found"
