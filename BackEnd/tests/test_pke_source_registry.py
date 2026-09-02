"""
Tests for the Pakistan Knowledge Engine source registry (PKE §5/§6/§7).

Coverage:
- PKESource model field defaults and helpers
- source_registry_service: create, read, list, filter, update_access_status
- Validation rules (invalid authority_level, domain, scope, URL, etc.)
- Access review status gates (only APPROVED sources returned by list_approved)
- Duplicate source_id prevention
- source_to_dict serialization
- Seed data integrity (all entries in pke_sources.json are internally valid)
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from knowledge_engine.pke_source_registry import PKESource
from knowledge_engine.source_registry_service import (
    VALID_ACCESS_STATUSES,
    VALID_AUTHORITY_LEVELS,
    VALID_DOMAINS,
    VALID_GEOGRAPHIC_SCOPES,
    VALID_SOURCE_TYPES,
    SourceRegistryError,
    create_source,
    get_source,
    get_source_by_pk,
    list_approved_sources,
    list_sources,
    source_to_dict,
    update_access_status,
)

SEED_FILE = (
    Path(__file__).resolve().parents[2] / "data" / "seed" / "pke_sources.json"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make(db, **overrides):
    """Create a minimal valid source entry."""
    defaults = dict(
        source_id="TEST-SRC-01",
        name="Test Source",
        base_url="https://example.gov.pk",
        authority_level="L1",
        source_type="OFFICIAL_GOVERNMENT",
        domains="universities",
        geographic_scope="karachi",
        access_review_status="APPROVED",
        retrieval_method="direct_fetch",
    )
    defaults.update(overrides)
    return create_source(db, **defaults)


# ---------------------------------------------------------------------------
# Model — field defaults and helpers
# ---------------------------------------------------------------------------


class TestPKESourceModel:
    def test_default_access_review_status(self, db_session):
        entry = PKESource(
            source_id="X-01",
            name="X",
            base_url="https://x.pk",
            authority_level="L2",
            source_type="SECONDARY_PORTAL",
            domains="jobs",
            geographic_scope="nationwide",
        )
        assert entry.access_review_status == "PENDING_REVIEW"

    def test_confidence_float_conversion(self, db_session):
        entry = PKESource(
            source_id="X-01",
            name="X",
            base_url="https://x.pk",
            authority_level="L1",
            source_type="OFFICIAL_GOVERNMENT",
            domains="schools",
            geographic_scope="islamabad",
            source_confidence=90,
        )
        assert entry.confidence_float == pytest.approx(0.90)

    def test_confidence_float_none_when_unset(self, db_session):
        entry = PKESource(
            source_id="X-01",
            name="X",
            base_url="https://x.pk",
            authority_level="L1",
            source_type="OFFICIAL_GOVERNMENT",
            domains="schools",
            geographic_scope="islamabad",
        )
        assert entry.confidence_float is None

    def test_domain_list_helper(self, db_session):
        entry = PKESource(
            source_id="X-01",
            name="X",
            base_url="https://x.pk",
            authority_level="L1",
            source_type="OFFICIAL_GOVERNMENT",
            domains="universities,programs,scholarships",
            geographic_scope="karachi",
        )
        assert entry.domain_list == ["universities", "programs", "scholarships"]

    def test_is_approved_true_when_approved(self, db_session):
        entry = PKESource(
            source_id="X-01",
            name="X",
            base_url="https://x.pk",
            authority_level="L1",
            source_type="OFFICIAL_GOVERNMENT",
            domains="schools",
            geographic_scope="islamabad",
            access_review_status="APPROVED",
        )
        assert entry.is_approved_for_ingestion is True

    def test_is_approved_false_for_pending(self, db_session):
        entry = PKESource(
            source_id="X-01",
            name="X",
            base_url="https://x.pk",
            authority_level="L2",
            source_type="SECONDARY_PORTAL",
            domains="jobs",
            geographic_scope="nationwide",
            access_review_status="PENDING_REVIEW",
        )
        assert entry.is_approved_for_ingestion is False


# ---------------------------------------------------------------------------
# Service — create
# ---------------------------------------------------------------------------


class TestCreateSource:
    def test_create_valid_source(self, db_session):
        entry = _make(db_session)
        assert entry.id is not None
        assert entry.source_id == "TEST-SRC-01"
        assert entry.authority_level == "L1"
        assert entry.geographic_scope == "karachi"

    def test_create_stores_all_fields(self, db_session):
        entry = _make(
            db_session,
            source_id="TEST-SRC-02",
            name="Full Source",
            base_url="https://full.gov.pk",
            authority_level="L2",
            source_type="SECONDARY_PORTAL",
            domains="jobs,internships",
            geographic_scope="lahore",
            access_review_status="PENDING_REVIEW",
            retrieval_method=None,
            has_official_api=True,
            is_reachable=True,
            last_checked=date(2026, 9, 1),
            source_confidence=75,
            notes="Test notes",
        )
        assert entry.authority_level == "L2"
        assert entry.has_official_api is True
        assert entry.source_confidence == 75
        assert entry.confidence_float == pytest.approx(0.75)
        assert entry.notes == "Test notes"
        assert entry.last_checked == date(2026, 9, 1)

    def test_duplicate_source_id_raises(self, db_session):
        _make(db_session)
        with pytest.raises(SourceRegistryError, match="already exists"):
            _make(db_session)

    def test_invalid_authority_level_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="authority_level"):
            _make(db_session, source_id="X-01", authority_level="L5")

    def test_invalid_source_type_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="source_type"):
            _make(db_session, source_id="X-01", source_type="FAKE_TYPE")

    def test_invalid_domain_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="Unknown domains"):
            _make(db_session, source_id="X-01", domains="gaming,esports")

    def test_partial_invalid_domain_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="Unknown domains"):
            _make(db_session, source_id="X-01", domains="universities,INVALID")

    def test_empty_domains_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="at least one"):
            _make(db_session, source_id="X-01", domains="")

    def test_invalid_geographic_scope_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="geographic_scope"):
            _make(db_session, source_id="X-01", geographic_scope="rawalpindi")

    def test_invalid_access_status_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="access_review_status"):
            _make(db_session, source_id="X-01", access_review_status="MAYBE")

    def test_invalid_retrieval_method_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="retrieval_method"):
            _make(db_session, source_id="X-01", retrieval_method="telepathy")

    def test_invalid_url_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="base_url"):
            _make(db_session, source_id="X-01", base_url="not-a-url")

    def test_invalid_confidence_above_100_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="confidence"):
            _make(db_session, source_id="X-01", source_confidence=101)

    def test_invalid_confidence_below_0_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="confidence"):
            _make(db_session, source_id="X-01", source_confidence=-1)

    def test_confidence_zero_is_valid(self, db_session):
        entry = _make(db_session, source_confidence=0)
        assert entry.source_confidence == 0
        assert entry.confidence_float == pytest.approx(0.0)

    def test_confidence_100_is_valid(self, db_session):
        entry = _make(db_session, source_confidence=100)
        assert entry.confidence_float == pytest.approx(1.0)

    def test_multi_domain_source(self, db_session):
        entry = _make(
            db_session,
            source_id="MULTI-01",
            domains="universities,programs,scholarships",
        )
        assert set(entry.domain_list) == {"universities", "programs", "scholarships"}

    def test_all_valid_geographic_scopes(self, db_session):
        for i, scope in enumerate(sorted(VALID_GEOGRAPHIC_SCOPES)):
            entry = _make(
                db_session,
                source_id=f"SCOPE-{i:02d}",
                geographic_scope=scope,
            )
            assert entry.geographic_scope == scope

    def test_all_valid_authority_levels(self, db_session):
        for i, level in enumerate(sorted(VALID_AUTHORITY_LEVELS)):
            entry = _make(
                db_session,
                source_id=f"LEVEL-{i:02d}",
                authority_level=level,
                access_review_status="PENDING_REVIEW",
            )
            assert entry.authority_level == level


# ---------------------------------------------------------------------------
# Service — read
# ---------------------------------------------------------------------------


class TestGetSource:
    def test_get_by_source_id(self, db_session):
        _make(db_session)
        found = get_source(db_session, "TEST-SRC-01")
        assert found is not None
        assert found.source_id == "TEST-SRC-01"

    def test_get_by_source_id_missing_returns_none(self, db_session):
        assert get_source(db_session, "DOES-NOT-EXIST") is None

    def test_get_by_pk(self, db_session):
        entry = _make(db_session)
        found = get_source_by_pk(db_session, entry.id)
        assert found is not None
        assert found.id == entry.id

    def test_get_by_pk_missing_returns_none(self, db_session):
        assert get_source_by_pk(db_session, 999999) is None


# ---------------------------------------------------------------------------
# Service — list / filter
# ---------------------------------------------------------------------------


class TestListSources:
    def _seed(self, db_session):
        _make(db_session, source_id="A-01", authority_level="L1", geographic_scope="karachi")
        _make(db_session, source_id="A-02", authority_level="L2", geographic_scope="lahore",
              source_type="SECONDARY_PORTAL", domains="jobs", access_review_status="PENDING_REVIEW")
        _make(db_session, source_id="A-03", authority_level="L1", geographic_scope="islamabad",
              domains="schools")

    def test_list_all_returns_all(self, db_session):
        self._seed(db_session)
        result = list_sources(db_session)
        assert len(result) == 3

    def test_filter_by_authority_level(self, db_session):
        self._seed(db_session)
        result = list_sources(db_session, authority_level="L1")
        assert len(result) == 2
        assert all(s.authority_level == "L1" for s in result)

    def test_filter_by_domain(self, db_session):
        self._seed(db_session)
        result = list_sources(db_session, domain="schools")
        assert len(result) == 1
        assert result[0].source_id == "A-03"

    def test_filter_by_geographic_scope(self, db_session):
        self._seed(db_session)
        result = list_sources(db_session, geographic_scope="lahore")
        assert len(result) == 1
        assert result[0].source_id == "A-02"

    def test_filter_by_access_review_status(self, db_session):
        self._seed(db_session)
        result = list_sources(db_session, access_review_status="PENDING_REVIEW")
        assert len(result) == 1
        assert result[0].source_id == "A-02"

    def test_list_approved_returns_only_approved(self, db_session):
        self._seed(db_session)
        approved = list_approved_sources(db_session)
        # A-01 and A-03 are APPROVED; A-02 is PENDING_REVIEW
        assert len(approved) == 2
        assert all(s.is_approved_for_ingestion for s in approved)

    def test_list_approved_with_domain_filter(self, db_session):
        self._seed(db_session)
        approved = list_approved_sources(db_session, domain="universities")
        # Only A-01 has domain "universities" and is APPROVED
        assert len(approved) == 1
        assert approved[0].source_id == "A-01"

    def test_list_approved_with_scope_filter(self, db_session):
        self._seed(db_session)
        approved = list_approved_sources(db_session, geographic_scope="islamabad")
        assert len(approved) == 1
        assert approved[0].source_id == "A-03"

    def test_empty_registry_returns_empty(self, db_session):
        assert list_sources(db_session) == []
        assert list_approved_sources(db_session) == []


# ---------------------------------------------------------------------------
# Service — update_access_status
# ---------------------------------------------------------------------------


class TestUpdateAccessStatus:
    def test_update_to_approved(self, db_session):
        _make(db_session, access_review_status="PENDING_REVIEW")
        updated = update_access_status(db_session, "TEST-SRC-01", "APPROVED")
        assert updated.access_review_status == "APPROVED"
        assert updated.is_approved_for_ingestion is True

    def test_update_to_blocked(self, db_session):
        _make(db_session)
        updated = update_access_status(db_session, "TEST-SRC-01", "BLOCKED")
        assert updated.access_review_status == "BLOCKED"
        assert updated.is_approved_for_ingestion is False

    def test_update_sets_tos_review_url(self, db_session):
        _make(db_session)
        updated = update_access_status(
            db_session,
            "TEST-SRC-01",
            "MANUAL_ONLY",
            tos_review_url="https://internal/tos-review/TEST-SRC-01",
            notes="Reviewed 2026-09-01: ToS prohibits bulk scraping.",
        )
        assert updated.tos_review_url == "https://internal/tos-review/TEST-SRC-01"
        assert "ToS" in updated.notes

    def test_update_sets_reachability_and_date(self, db_session):
        _make(db_session)
        updated = update_access_status(
            db_session,
            "TEST-SRC-01",
            "APPROVED",
            is_reachable=True,
            last_checked=date(2026, 9, 1),
        )
        assert updated.is_reachable is True
        assert updated.last_checked == date(2026, 9, 1)

    def test_update_invalid_status_raises(self, db_session):
        _make(db_session)
        with pytest.raises(SourceRegistryError, match="access_review_status"):
            update_access_status(db_session, "TEST-SRC-01", "UNKNOWN_STATUS")

    def test_update_nonexistent_source_raises(self, db_session):
        with pytest.raises(SourceRegistryError, match="not found"):
            update_access_status(db_session, "DOES-NOT-EXIST", "APPROVED")

    def test_update_persisted_to_database(self, db_session):
        _make(db_session, access_review_status="PENDING_REVIEW")
        update_access_status(db_session, "TEST-SRC-01", "DISCOVERY_ONLY")
        reloaded = get_source(db_session, "TEST-SRC-01")
        assert reloaded.access_review_status == "DISCOVERY_ONLY"


# ---------------------------------------------------------------------------
# Service — source_to_dict serialization
# ---------------------------------------------------------------------------


class TestSourceToDict:
    def test_dict_contains_all_required_keys(self, db_session):
        entry = _make(
            db_session,
            domains="universities,programs",
            source_confidence=90,
            last_checked=date(2026, 9, 1),
        )
        d = source_to_dict(entry)
        required_keys = {
            "id", "source_id", "name", "base_url", "authority_level",
            "source_type", "domains", "geographic_scope",
            "access_review_status", "is_approved_for_ingestion",
            "retrieval_method", "has_official_api", "is_reachable",
            "last_checked", "confidence", "notes", "tos_review_url",
            "created_at", "updated_at",
        }
        assert required_keys.issubset(d.keys())

    def test_domains_returned_as_list(self, db_session):
        entry = _make(db_session, domains="universities,programs")
        d = source_to_dict(entry)
        assert isinstance(d["domains"], list)
        assert set(d["domains"]) == {"universities", "programs"}

    def test_confidence_returned_as_float(self, db_session):
        entry = _make(db_session, source_confidence=90)
        d = source_to_dict(entry)
        assert d["confidence"] == pytest.approx(0.90)

    def test_confidence_none_when_unset(self, db_session):
        entry = _make(db_session)
        d = source_to_dict(entry)
        assert d["confidence"] is None

    def test_last_checked_iso_format(self, db_session):
        entry = _make(db_session, last_checked=date(2026, 9, 1))
        d = source_to_dict(entry)
        assert d["last_checked"] == "2026-09-01"

    def test_is_approved_for_ingestion_field(self, db_session):
        entry = _make(db_session, access_review_status="APPROVED")
        d = source_to_dict(entry)
        assert d["is_approved_for_ingestion"] is True

        entry2 = _make(
            db_session,
            source_id="X-02",
            access_review_status="PENDING_REVIEW",
        )
        d2 = source_to_dict(entry2)
        assert d2["is_approved_for_ingestion"] is False


# ---------------------------------------------------------------------------
# Seed data integrity
# ---------------------------------------------------------------------------


class TestSeedDataIntegrity:
    """Verify that every entry in pke_sources.json is internally consistent.

    These tests do NOT fetch any URLs — they only parse and validate the
    static seed JSON.
    """

    @pytest.fixture(autouse=True)
    def load_seed(self):
        self.payload = json.loads(SEED_FILE.read_text(encoding="utf-8"))
        self.sources = self.payload["sources"]

    def test_seed_file_exists(self):
        assert SEED_FILE.exists(), f"Seed file not found: {SEED_FILE}"

    def test_seed_has_sources(self):
        assert len(self.sources) > 0

    def test_all_source_ids_unique(self):
        ids = [s["source_id"] for s in self.sources]
        assert len(ids) == len(set(ids)), "Duplicate source_id in seed file"

    def test_all_authority_levels_valid(self):
        for s in self.sources:
            assert s["authority_level"] in VALID_AUTHORITY_LEVELS, (
                f"{s['source_id']}: invalid authority_level {s['authority_level']!r}"
            )

    def test_all_source_types_valid(self):
        for s in self.sources:
            assert s["source_type"] in VALID_SOURCE_TYPES, (
                f"{s['source_id']}: invalid source_type {s['source_type']!r}"
            )

    def test_all_domains_valid(self):
        for s in self.sources:
            domain_list = [d.strip() for d in s["domains"].split(",") if d.strip()]
            for d in domain_list:
                assert d in VALID_DOMAINS, (
                    f"{s['source_id']}: unknown domain {d!r}"
                )

    def test_all_geographic_scopes_valid(self):
        for s in self.sources:
            assert s["geographic_scope"] in VALID_GEOGRAPHIC_SCOPES, (
                f"{s['source_id']}: invalid scope {s['geographic_scope']!r}"
            )

    def test_all_access_statuses_valid(self):
        for s in self.sources:
            assert s["access_review_status"] in VALID_ACCESS_STATUSES, (
                f"{s['source_id']}: invalid access status {s['access_review_status']!r}"
            )

    def test_all_base_urls_are_http(self):
        for s in self.sources:
            assert s["base_url"].startswith(("http://", "https://")), (
                f"{s['source_id']}: base_url {s['base_url']!r} is not http(s)"
            )

    def test_all_confidences_in_range(self):
        for s in self.sources:
            conf = s.get("source_confidence")
            if conf is not None:
                assert 0 <= conf <= 100, (
                    f"{s['source_id']}: source_confidence {conf} out of 0-100 range"
                )

    def test_l2_sources_not_auto_approved(self):
        """L2 sources must not be APPROVED unless an access review was done."""
        for s in self.sources:
            if s["authority_level"] == "L2":
                assert s["access_review_status"] != "APPROVED", (
                    f"{s['source_id']}: L2 source is APPROVED without documented review"
                )

    def test_linkedin_is_discovery_only(self):
        """LinkedIn must never be APPROVED per PKE §6.4."""
        linkedin = next(
            (s for s in self.sources if s["source_id"] == "JOB-LINKEDIN-01"),
            None,
        )
        assert linkedin is not None, "JOB-LINKEDIN-01 missing from seed"
        assert linkedin["access_review_status"] == "DISCOVERY_ONLY"

    def test_l1_government_sources_cover_all_three_cities(self):
        """Each of the three MVP cities must have at least one L1 government source."""
        cities = {"karachi", "lahore", "islamabad"}
        covered = {
            s["geographic_scope"]
            for s in self.sources
            if s["authority_level"] == "L1"
            and s["source_type"] == "OFFICIAL_GOVERNMENT"
            and s["geographic_scope"] in cities
        }
        missing = cities - covered
        assert not missing, f"No L1 government source for cities: {missing}"

    def test_each_pke_domain_has_at_least_one_source(self):
        """All 12 PKE domains must have at least one source entry."""
        covered = set()
        for s in self.sources:
            for d in s["domains"].split(","):
                covered.add(d.strip())
        missing = VALID_DOMAINS - covered
        assert not missing, f"PKE domains with no source: {missing}"

    def test_seed_can_be_inserted_into_database(self, db_session):
        """All seed rows are valid and insertable without errors."""
        for record in self.sources:
            last_checked = None
            if record.get("last_checked"):
                last_checked = date.fromisoformat(record["last_checked"])

            retrieval_method = record.get("retrieval_method")
            # null JSON becomes None — ensure it maps to a valid value
            if retrieval_method not in {
                "direct_fetch", "html_table", "csv_import",
                "json_api", "hf_dataset", "manual", None,
            }:
                raise AssertionError(
                    f"{record['source_id']}: invalid retrieval_method {retrieval_method!r}"
                )

            entry = create_source(
                db_session,
                source_id=record["source_id"],
                name=record["name"],
                base_url=record["base_url"],
                authority_level=record["authority_level"],
                source_type=record["source_type"],
                domains=record["domains"],
                geographic_scope=record["geographic_scope"],
                access_review_status=record["access_review_status"],
                retrieval_method=retrieval_method,
                has_official_api=bool(record.get("has_official_api", False)),
                is_reachable=record.get("is_reachable"),
                last_checked=last_checked,
                source_confidence=record.get("source_confidence"),
                notes=record.get("notes"),
            )
            assert entry.id is not None, f"Failed to insert {record['source_id']}"

        # Confirm all 42 rows are in the database
        all_entries = list_sources(db_session)
        assert len(all_entries) == len(self.sources)
