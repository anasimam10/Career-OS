"""
Tests for PKE staging records model and persistence (Step 3).
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from knowledge_engine.staging import PKEStagingRecord
from ingestion.ingestion_service import run_url_ingestion
from models.source import Source, SourceDocument, IngestionItem
from schemas.admin import IngestUrlRequest


def test_create_pke_staging_record(db_session):
    record = PKEStagingRecord(
        domain="universities",
        extracted_json='{"name": "NUST", "city": "Islamabad"}',
        source_url="https://nust.edu.pk",
        verification_status="CANDIDATE"
    )
    db_session.add(record)
    db_session.commit()
    
    assert record.id is not None
    assert record.domain == "universities"
    assert record.verification_status == "CANDIDATE"
    assert isinstance(record.created_at, datetime)


def test_staging_record_defaults_to_candidate(db_session):
    record = PKEStagingRecord(
        domain="schools",
        extracted_json='{"name": "Some School"}',
        source_url="https://school.pk",
    )
    db_session.add(record)
    db_session.commit()
    
    assert record.verification_status == "CANDIDATE"


def test_ingestion_pipeline_stores_staging_record_for_new_domains(db_session, monkeypatch):
    """Ensure that non-opportunity domains use PKEStagingRecord instead of Opportunity."""
    
    # Mock fetching
    def mock_fetch(url):
        return "<html><body>Mock Content</body></html>"
    
    # Mock extraction routing
    from knowledge_engine.schemas import UniversityExtraction
    def mock_extract(domain, content, url):
        return UniversityExtraction(name="Mock Uni", city="Lahore")
        
    monkeypatch.setattr("ingestion.ingestion_service._fetch_url", mock_fetch)
    monkeypatch.setattr("ingestion.ingestion_service.route_extraction", mock_extract)
    
    result = run_url_ingestion(
        db_session,
        urls=["https://example.com/uni"],
        source_type="OFFICIAL_UNIVERSITY",
        domain="universities"
    )
    
    assert result["queued_count"] == 1
    
    # Check that a staging record was created
    staging = db_session.query(PKEStagingRecord).first()
    assert staging is not None
    assert staging.domain == "universities"
    assert staging.source_url == "https://example.com/uni"
    assert staging.verification_status == "CANDIDATE"
    
    # Ensure no Opportunity was created
    from models.opportunity import Opportunity
    opps = db_session.query(Opportunity).count()
    assert opps == 0
    
    # Ensure IngestionItem marked as STORED
    item = db_session.query(IngestionItem).first()
    assert item.status == "STORED"
