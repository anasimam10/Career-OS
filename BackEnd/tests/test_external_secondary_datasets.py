"""
Tests for External Secondary CSV Datasets Integration (PKE Provenance & Staging).
"""

import json
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

from database import SessionLocal
from models.university import University
from models.source import Source
from knowledge_engine.pke_source_registry import PKESource
from knowledge_engine.staging import PKEStagingRecord
from retrieval.university_retrieval import (
    search_universities,
    get_university_secondary_intellectual_capital,
    get_public_universities_macro_statistics,
)
from scripts.import_external_secondary_datasets import (
    find_dataset_path,
    normalize_text,
    UNIVERSITY_ALIASES,
    register_pke_sources,
    import_public_universities_macro_csv,
    import_cs_intellectual_capital_csv,
    run_import,
    SOURCE_PUBUNIV_ID,
    SOURCE_CS_FACULTY_ID,
)


def test_csv_file_resolution_and_encodings():
    """Verify both datasets exist and resolve correctly."""
    f1 = find_dataset_path("number-of-public-universities-in-pakistan.csv")
    f2 = find_dataset_path("pakistan-intellectual-capital-computer-science-ver-1.csv")
    assert f1.exists() and f1.is_file()
    assert f2.exists() and f2.is_file()

    # Test Dataset 1 encoding (utf-8-sig)
    with open(f1, "r", encoding="utf-8-sig") as f:
        first_line = f.readline()
        assert "Year" in first_line
        assert "Total" in first_line

    # Test Dataset 2 encoding (latin1)
    with open(f2, "r", encoding="latin1") as f:
        first_line = f.readline()
        assert "Teacher Name" in first_line
        assert "University Currently Teaching" in first_line


def test_text_normalization_and_alias_mapping():
    """Test text normalization and Pakistani university alias mappings."""
    assert normalize_text("  N.U.S.T. (Islamabad)  ") == "nust islamabad"
    assert normalize_text("FAST-NUCES") == "fast nuces"

    assert UNIVERSITY_ALIASES[normalize_text("FAST")] == "fast-nuces"
    assert UNIVERSITY_ALIASES[normalize_text("NUST")] == "nust"
    assert UNIVERSITY_ALIASES[normalize_text("LUMS")] == "lums"
    assert UNIVERSITY_ALIASES[normalize_text("COMSATS")] == "comsats"
    assert UNIVERSITY_ALIASES[normalize_text("UET Lahore")] == "uet-lahore"
    assert UNIVERSITY_ALIASES[normalize_text("NED")] == "ned"
    assert UNIVERSITY_ALIASES[normalize_text("IBA")] == "iba-karachi"


def test_provenance_sources_registration(db_session: Session):
    """Verify external secondary datasets are registered with L2 authority and EXTERNAL_SECONDARY type."""
    pke_src1, pke_src2 = register_pke_sources(db_session)

    # 1. Dataset 1
    assert pke_src1.source_id == SOURCE_PUBUNIV_ID
    assert pke_src1.authority_level == "L2"
    assert pke_src1.source_type == "EXTERNAL_SECONDARY"
    assert "macro_statistics" in pke_src1.domains
    assert pke_src1.access_review_status == "APPROVED"

    op_src1 = db_session.query(Source).filter(Source.source_url == pke_src1.base_url).first()
    assert op_src1 is not None
    assert op_src1.source_type == "EXTERNAL_SECONDARY"
    assert op_src1.classification == "SECONDARY"

    # 2. Dataset 2
    assert pke_src2.source_id == SOURCE_CS_FACULTY_ID
    assert pke_src2.authority_level == "L2"
    assert pke_src2.source_type == "EXTERNAL_SECONDARY"
    assert "faculty_intellectual_capital" in pke_src2.domains
    assert pke_src2.access_review_status == "APPROVED"

    op_src2 = db_session.query(Source).filter(Source.source_url == pke_src2.base_url).first()
    assert op_src2 is not None
    assert op_src2.source_type == "EXTERNAL_SECONDARY"
    assert op_src2.classification == "SECONDARY"


def test_primary_pke_precedence_and_zero_overwrites(db_session: Session):
    """PRIMARY PKE DATA WINS: Primary university attributes must NEVER be overwritten or downgraded."""
    # Create or verify primary NUST record
    nust = db_session.query(University).filter(University.slug == "nust").first()
    if not nust:
        nust = University(
            name="National University of Sciences and Technology",
            short_name="NUST",
            slug="nust",
            city="Islamabad",
            province="Islamabad",
            type="PUBLIC",
            hec_recognized=True,
            verification_status="VERIFIED",
        )
        db_session.add(nust)
        db_session.commit()
        db_session.refresh(nust)

    orig_name = nust.name
    orig_type = nust.type
    orig_city = nust.city
    orig_status = nust.verification_status

    # Run import
    pke_src1, pke_src2 = register_pke_sources(db_session)
    f2_path = find_dataset_path("pakistan-intellectual-capital-computer-science-ver-1.csv")
    import_cs_intellectual_capital_csv(db_session, f2_path, pke_src2, dry_run=False)

    # Re-fetch NUST and assert primary fields remain unchanged
    db_session.refresh(nust)
    assert nust.name == orig_name
    assert nust.type == orig_type
    assert nust.city == orig_city
    assert nust.verification_status == orig_status


def test_idempotency_of_importer(db_session: Session):
    """Running importer multiple times must be strictly idempotent (0 duplicate rows)."""
    pke_src1, pke_src2 = register_pke_sources(db_session)
    f1_path = find_dataset_path("number-of-public-universities-in-pakistan.csv")

    # Run 1
    stats1 = import_public_universities_macro_csv(db_session, f1_path, pke_src1, dry_run=False)
    assert stats1["rows_found"] == 11

    # Run 2 (Must skip all existing rows)
    stats2 = import_public_universities_macro_csv(db_session, f1_path, pke_src1, dry_run=False)
    assert stats2["rows_found"] == 11
    assert stats2["rows_imported"] == 0
    assert stats2["rows_skipped"] == 11
    assert stats2["rows_rejected"] == 0


def test_student_visibility_boundary(db_session: Session):
    """Staged secondary/candidate records must NEVER appear in student-facing university search results."""
    # Seed a candidate university only in staging
    cand_key = "candidate_uni:test_unverified_uni"
    cand_record = PKEStagingRecord(
        domain="university_candidates",
        extracted_json=json.dumps({"name": "Unverified Test University", "city": "Quetta"}),
        source_url="local://test",
        dedup_key=cand_key,
        verification_status="CANDIDATE",
    )
    db_session.add(cand_record)
    db_session.commit()

    # Search universities via student-facing function
    results = search_universities(db_session, query="Unverified Test University")
    # Must NOT find the unverified university
    assert len(results) == 0

    # Ensure search only returns VERIFIED / VALIDATED universities
    all_results = search_universities(db_session)
    for uni in all_results:
        assert uni["verification_status"] in ("VERIFIED", "VALIDATED")


def test_retrieval_of_secondary_intellectual_capital(db_session: Session):
    """Verify secondary intellectual capital can be retrieved with clear secondary provenance."""
    # Seed primary university
    nust = db_session.query(University).filter(University.slug == "nust").first()
    if not nust:
        nust = University(
            name="National University of Sciences and Technology",
            short_name="NUST",
            slug="nust",
            city="Islamabad",
            verification_status="VERIFIED",
        )
        db_session.add(nust)
        db_session.commit()

    # Seed secondary enrichment staging record
    enrich_key = f"enrichment:university:{nust.id}"
    enrich_json = json.dumps({
        "university_id": nust.id,
        "university_name": nust.name,
        "university_slug": nust.slug,
        "cs_faculty_count": 25,
        "phd_faculty_count": 18,
        "departments": ["Computing", "Software Engineering"],
        "top_specializations": ["Artificial Intelligence", "Computer Vision"],
        "provenance": {
            "source_id": SOURCE_CS_FACULTY_ID,
            "dataset": "Pakistan Intellectual Capital - Computer Science",
        }
    })
    rec = db_session.query(PKEStagingRecord).filter(PKEStagingRecord.dedup_key == enrich_key).first()
    if not rec:
        rec = PKEStagingRecord(
            domain="university_secondary_enrichment",
            extracted_json=enrich_json,
            source_url="local://test",
            dedup_key=enrich_key,
            verification_status="SECONDARY",
        )
        db_session.add(rec)
        db_session.commit()

    # Query helper
    data = get_university_secondary_intellectual_capital(db_session, "nust")
    assert data is not None
    assert data["university_slug"] == "nust"
    assert data["cs_faculty_count"] == 25
    assert data["phd_faculty_count"] == 18
    assert data["is_primary"] is False
    assert data["authority_level"] == "L2"
    assert data["source_type"] == "EXTERNAL_SECONDARY"
    assert "Supplementary external secondary dataset" in data["data_provenance_note"]


def test_retrieval_of_macro_statistics(db_session: Session):
    """Verify macro statistics retrieval."""
    stat_key = "macro_stat:pub_univ:2017-18"
    rec = db_session.query(PKEStagingRecord).filter(PKEStagingRecord.dedup_key == stat_key).first()
    if not rec:
        rec = PKEStagingRecord(
            domain="macro_statistics",
            extracted_json=json.dumps({"year": "2017-18", "total_public_universities": 108}),
            source_url="local://test",
            dedup_key=stat_key,
            verification_status="SECONDARY",
        )
        db_session.add(rec)
        db_session.commit()

    stats = get_public_universities_macro_statistics(db_session)
    assert len(stats) > 0
    match = next((s for s in stats if s.get("year") == "2017-18"), None)
    assert match is not None
    assert match["source_type"] == "EXTERNAL_SECONDARY"
    assert match["authority_level"] == "L2"


def test_mcp_secondary_intellectual_capital_tool(db_session: Session):
    """Verify the MCP tool get_university_faculty_intellectual_capital."""
    from Mcp.pke_server import get_university_faculty_intellectual_capital

    res = get_university_faculty_intellectual_capital("non-existent-university-slug")
    assert res["found"] is False
    assert res["source_type"] == "EXTERNAL_SECONDARY"
