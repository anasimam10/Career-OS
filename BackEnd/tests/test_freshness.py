"""
Phase 5 tests — Freshness + visibility trust rules (master §10/§11/§22).

The three trust gates every student-facing query must apply:

1. verification — only VALIDATED/VERIFIED records are visible; CANDIDATE
   records (e.g. everything the ingestion pipeline creates) stay hidden
   until an admin verifies them (stage 9)
2. active — inactive records never appear
3. freshness — expired deadlines (deadline < today) are filtered
   server-side; records verified more than 30 days ago carry the §10
   data_freshness "unverified" label (semantics = master's STALE)
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from database import SessionLocal
from ingestion.ingestion_service import refresh_sources
from models.opportunity import Opportunity, SportsOpportunity
from models.source import Source
from services.matching_service import data_freshness

# The Mcp package lives at the repository root (conftest imports main first).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Mcp import db_access  # noqa: E402
from Mcp import opportunity_server as opportunity_tools  # noqa: E402
from tests.conftest import TestingSessionLocal  # noqa: E402


def soon(days: int) -> date:
    return date.today() + timedelta(days=days)


# ---------------------------------------------------------------------------
# matching_service.data_freshness unit tests (§10 30-day rule)
# ---------------------------------------------------------------------------


class TestDataFreshnessLabel:
    def test_none_is_fresh(self):
        assert data_freshness(None) is None

    def test_recent_is_unlabeled(self):
        assert data_freshness(date.today() - timedelta(days=5)) is None

    def test_older_than_30_days_is_unverified(self):
        assert data_freshness(date.today() - timedelta(days=31)) == "unverified"

    def test_exactly_30_days_is_still_fresh(self):
        assert data_freshness(date.today() - timedelta(days=30)) is None

    def test_iso_string_input(self):
        assert data_freshness(date.today().isoformat()) is None

    def test_garbage_string_is_treated_as_fresh(self):
        # Never crash, never fabricate a stale claim from unparseable data.
        assert data_freshness("not-a-date") is None


# ---------------------------------------------------------------------------
# Visibility gate 1 — CANDIDATE records stay hidden
# ---------------------------------------------------------------------------


class TestCandidateRecordsHidden:
    @pytest.fixture
    def candidate_db(self, db_session):
        def add(**kwargs):
            row = Opportunity(
                type="internship",
                title=kwargs.pop("title"),
                verification_status="CANDIDATE",
                is_active=True,
                **kwargs,
            )
            db_session.add(row)
            db_session.commit()
            return row

        add(title="Future Candidate Intern", deadline=soon(30))
        add(title="No-Deadline Candidate Job", deadline=None)
        add(title="Candidate Scholarship", deadline=soon(90), last_verified=date.today())
        db_access.set_session_factory(TestingSessionLocal)
        yield db_session
        db_access.set_session_factory(SessionLocal)

    def test_listing_hides_all_candidates(self, client, candidate_db):
        response = client.get("/api/v1/opportunities")
        body = response.json()
        if isinstance(body, dict):
            assert body["opportunities"] == []
        else:
            assert body == []

    def test_mcp_tool_hides_candidates(self, candidate_db):
        result = opportunity_tools.search_internships(
            skills=None, city="Karachi"
        )
        assert result["count"] == 0


class TestSportsCandidateHidden:
    def test_sports_listing_hides_candidate(self, client, db_session):
        db_session.add(
            SportsOpportunity(
                sport="Badminton",
                type="trial",
                title="Candidate Badminton Trial (template)",
                location="Karachi",
                verification_status="CANDIDATE",
                is_active=True,
            )
        )
        db_session.commit()
        response = client.get("/api/v1/sports")
        body = response.json()
        titles = (
            [s["title"] for s in body["sports_opportunities"]]
            if isinstance(body, dict)
            else [s["title"] for s in body]
        )
        assert "Candidate Badminton Trial (template)" not in titles


# ---------------------------------------------------------------------------
# Visibility gate 3 — expired deadlines filtered server-side
# ---------------------------------------------------------------------------


class TestExpiredDeadlines:
    @pytest.fixture
    def deadline_db(self, db_session):
        rows = [
            Opportunity(
                type="internship",
                title="Expired Internship",
                location="Karachi",
                deadline=date.today() - timedelta(days=1),
                verification_status="VALIDATED",
                is_active=True,
            ),
            Opportunity(
                type="internship",
                title="Deadline Today Internship",
                location="Karachi",
                deadline=date.today(),
                verification_status="VALIDATED",
                is_active=True,
            ),
            Opportunity(
                type="internship",
                title="Future Internship",
                location="Karachi",
                deadline=soon(5),
                verification_status="VALIDATED",
                is_active=True,
            ),
            Opportunity(
                type="internship",
                title="No Deadline Internship",
                location="Karachi",
                deadline=None,
                verification_status="VALIDATED",
                is_active=True,
            ),
        ]
        for row in rows:
            db_session.add(row)
        db_session.commit()
        db_access.set_session_factory(TestingSessionLocal)
        yield db_session
        db_access.set_session_factory(SessionLocal)

    def _titles(self, client):
        body = client.get("/api/v1/opportunities").json()
        if isinstance(body, dict):
            return [o["title"] for o in body["opportunities"]]
        return [o["title"] for o in body]

    def test_expired_hidden_others_visible(self, client, deadline_db):
        titles = self._titles(client)
        assert "Expired Internship" not in titles
        assert "Deadline Today Internship" in titles  # today still applies
        assert "Future Internship" in titles
        assert "No Deadline Internship" in titles  # no deadline never expires

    def test_mcp_tool_filters_expired(self, client, deadline_db):
        result = opportunity_tools.search_internships(skills=None, city="Karachi")
        titles = [r["title"] for r in result["results"]]
        assert "Expired Internship" not in titles
        assert "Future Internship" in titles


class TestSportsExpiredHidden:
    def test_sports_expired_hidden(self, client, db_session):
        db_session.add(
            SportsOpportunity(
                sport="Cricket",
                type="tournament",
                title="Past Cricket Cup (template)",
                location="Lahore",
                deadline=date.today() - timedelta(days=10),
                verification_status="VALIDATED",
                is_active=True,
            )
        )
        db_session.add(
            SportsOpportunity(
                sport="Cricket",
                type="tournament",
                title="Upcoming Cricket Cup (template)",
                location="Lahore",
                deadline=soon(10),
                verification_status="VALIDATED",
                is_active=True,
            )
        )
        db_session.commit()
        body = client.get("/api/v1/sports").json()
        titles = (
            [s["title"] for s in body["sports_opportunities"]]
            if isinstance(body, dict)
            else [s["title"] for s in body]
        )
        assert "Past Cricket Cup (template)" not in titles
        assert "Upcoming Cricket Cup (template)" in titles


# ---------------------------------------------------------------------------
# Freshness label in listings (§10)
# ---------------------------------------------------------------------------


class TestFreshnessLabelInListing:
    def test_stale_verified_record_labeled_unverified(self, client, db_session):
        db_session.add(
            Opportunity(
                type="internship",
                title="Old Verified Internship (template)",
                location="Karachi",
                deadline=soon(30),
                last_verified=date.today() - timedelta(days=45),
                verification_status="VALIDATED",
                is_active=True,
            )
        )
        db_session.add(
            Opportunity(
                type="internship",
                title="Fresh Verified Internship (template)",
                location="Karachi",
                deadline=soon(30),
                last_verified=date.today() - timedelta(days=3),
                verification_status="VALIDATED",
                is_active=True,
            )
        )
        db_session.commit()
        body = client.get("/api/v1/opportunities").json()
        items = body if isinstance(body, list) else body["opportunities"]
        by_title = {o["title"]: o["data_freshness"] for o in items}
        assert by_title["Old Verified Internship (template)"] == "unverified"
        assert by_title["Fresh Verified Internship (template)"] is None


# ---------------------------------------------------------------------------
# Refresh staleness window (master §12 mode C)
# ---------------------------------------------------------------------------


class TestRefreshStalenessWindow:
    def _source(self, db_session, *, days_ago, last_verified=None):
        db_session.add(
            Source(
                source_url=f"https://example.com/src{days_ago}-{last_verified}",
                source_type="OFFICIAL_COMPANY",
                retrieved_at=datetime_old(days_ago),
                last_verified=last_verified,
            )
        )
        db_session.commit()

    def test_source_older_than_seven_days_is_stale(self, db_session):
        self._source(db_session, days_ago=8)
        result = refresh_sources(db_session)
        assert result["queued_count"] == 1

    def test_fresh_source_not_stale(self, db_session):
        self._source(db_session, days_ago=1)
        result = refresh_sources(db_session)
        assert result["queued_count"] == 0

    def test_recent_last_verified_wins_over_old_retrieved_at(self, db_session):
        # COALESCE(last_verified, retrieved_at): a source verified 2 days
        # ago is NOT stale even if first retrieved 30 days ago.
        self._source(
            db_session,
            days_ago=30,
            last_verified=datetime_old(2),
        )
        result = refresh_sources(db_session)
        assert result["queued_count"] == 0


def datetime_old(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)
