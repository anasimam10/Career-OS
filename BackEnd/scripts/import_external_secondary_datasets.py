"""
Import External Secondary CSV Datasets into Career OS / PKE.

Datasets:
1. number-of-public-universities-in-pakistan.csv (Macro statistics)
2. pakistan-intellectual-capital-computer-science-ver-1.csv (Faculty intellectual capital)

PROVENANCE & PRIORITY RULES:
- Source Classification: L2, EXTERNAL_SECONDARY
- Primary PKE Data Wins: Primary university/program records are NEVER overwritten or downgraded.
- No Direct Ingestion of Unverified Institutions: Unmatched universities are staged as CANDIDATE (NEEDS_REVIEW).
- Idempotent: Running this script repeatedly does not create duplicate records.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure BackEnd is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal, init_db
from models.university import University, Program
from models.source import Source
from knowledge_engine.pke_source_registry import PKESource
from knowledge_engine.staging import PKEStagingRecord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("external_importer")

# Dataset 1 Metadata
SOURCE_PUBUNIV_ID = "EXT-STAT-PUBUNIV-01"
SOURCE_PUBUNIV_NAME = "Historical Statistics of Public Universities in Pakistan"
SOURCE_PUBUNIV_URL = "local://data/external/number-of-public-universities-in-pakistan.csv"

# Dataset 2 Metadata
SOURCE_CS_FACULTY_ID = "EXT-RES-CS-FACULTY-01"
SOURCE_CS_FACULTY_NAME = "Pakistan Intellectual Capital - Computer Science Faculty"
SOURCE_CS_FACULTY_URL = "local://data/external/pakistan-intellectual-capital-computer-science-ver-1.csv"


def find_dataset_path(filename: str) -> Path:
    """Resolve dataset path checking multiple potential folder locations."""
    candidates = [
        BACKEND_DIR / "data" / "external" / filename,
        BACKEND_DIR / "data external" / filename,
        BACKEND_DIR.parent / "data" / "external" / filename,
        BACKEND_DIR.parent / "BackEnd" / "data" / "external" / filename,
        BACKEND_DIR.parent / "BackEnd" / "data external" / filename,
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    raise FileNotFoundError(f"Could not locate external dataset {filename}. Checked: {candidates}")


def normalize_text(text: str) -> str:
    """Normalize string for robust deduplication and alias matching."""
    if not text:
        return ""
    # Remove dots so N.U.S.T. -> NUST, U.E.T. -> UET
    text = re.sub(r"\.(?=[A-Za-z]|\s|$)", "", text)
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


# Aliases mapping normalized external university strings to primary PKE slugs
UNIVERSITY_ALIASES: Dict[str, str] = {
    normalize_text("National University of Sciences and Technology"): "nust",
    normalize_text("National University of Sciences & Technology"): "nust",
    normalize_text("NUST"): "nust",
    normalize_text("National University of Computer and Emerging Sciences"): "fast-nuces",
    normalize_text("National University of Computer & Emerging Sciences"): "fast-nuces",
    normalize_text("FAST"): "fast-nuces",
    normalize_text("FAST NUCES"): "fast-nuces",
    normalize_text("FAST-NUCES"): "fast-nuces",
    normalize_text("Lahore University of Management Sciences"): "lums",
    normalize_text("LUMS"): "lums",
    normalize_text("COMSATS University"): "comsats",
    normalize_text("COMSATS University Islamabad"): "comsats",
    normalize_text("COMSATS Institute of Information Technology"): "comsats",
    normalize_text("COMSATS"): "comsats",
    normalize_text("CUI"): "comsats",
    normalize_text("Ghulam Ishaq Khan Institute of Engineering Sciences and Technology"): "giki",
    normalize_text("Ghulam Ishaq Khan Institute"): "giki",
    normalize_text("GIKI"): "giki",
    normalize_text("GIK Institute"): "giki",
    normalize_text("Pakistan Institute of Engineering and Applied Sciences"): "pieas",
    normalize_text("PIEAS"): "pieas",
    normalize_text("Institute of Business Administration"): "iba-karachi",
    normalize_text("Institute of Business Administration Karachi"): "iba-karachi",
    normalize_text("IBA"): "iba-karachi",
    normalize_text("IBA Karachi"): "iba-karachi",
    normalize_text("Aga Khan University"): "aku",
    normalize_text("AKU"): "aku",
    normalize_text("Dow University of Health Sciences"): "duhs",
    normalize_text("DUHS"): "duhs",
    normalize_text("King Edward Medical University"): "kemu",
    normalize_text("KEMU"): "kemu",
    normalize_text("University of Engineering and Technology Lahore"): "uet-lahore",
    normalize_text("University of Engineering & Technology Lahore"): "uet-lahore",
    normalize_text("UET Lahore"): "uet-lahore",
    normalize_text("University of the Punjab"): "punjab",
    normalize_text("Punjab University"): "punjab",
    normalize_text("PU"): "punjab",
    normalize_text("University of Karachi"): "karachi",
    normalize_text("UoK"): "karachi",
    normalize_text("NED University of Engineering and Technology"): "ned",
    normalize_text("NED University of Engineering & Technology"): "ned",
    normalize_text("NED"): "ned",
    normalize_text("Habib University"): "habib",
    normalize_text("HU"): "habib",
    normalize_text("Iqra University"): "iqra",
    normalize_text("Shaheed Zulfikar Ali Bhutto Institute of Science and Technology"): "szabist",
    normalize_text("SZABIST"): "szabist",
    normalize_text("Bahauddin Zakariya University"): "bzu",
    normalize_text("BZU"): "bzu",
    normalize_text("Mehran University of Engineering and Technology"): "muet",
    normalize_text("Mehran University of Engineering & Technology"): "muet",
    normalize_text("MUET"): "muet",
    normalize_text("Government College University Lahore"): "gcu-lahore",
    normalize_text("GCU Lahore"): "gcu-lahore",
    normalize_text("University of Peshawar"): "peshawar",
    normalize_text("UoP"): "peshawar",
    normalize_text("Bahria University"): "bahria",
    normalize_text("BU"): "bahria",
    normalize_text("Allama Iqbal Open University"): "aiou",
    normalize_text("AIOU"): "aiou",
    normalize_text("Quaid i Azam University"): "qau",
    normalize_text("Quaid e Azam University"): "qau",
    normalize_text("QAU"): "qau",
}


def register_pke_sources(db) -> Tuple[PKESource, PKESource]:
    """Ensure both datasets are registered in pke_sources and operational sources."""
    # 1. Dataset 1 Source
    pke_src1 = db.query(PKESource).filter(PKESource.source_id == SOURCE_PUBUNIV_ID).first()
    if not pke_src1:
        pke_src1 = PKESource(
            source_id=SOURCE_PUBUNIV_ID,
            name=SOURCE_PUBUNIV_NAME,
            base_url=SOURCE_PUBUNIV_URL,
            authority_level="L2",
            source_type="EXTERNAL_SECONDARY",
            domains="universities,macro_statistics",
            geographic_scope="nationwide",
            access_review_status="APPROVED",
            retrieval_method="csv_import",
            has_official_api=False,
            is_reachable=True,
            source_confidence=75,
            notes="Secondary aggregate macro statistics on the historical number of public universities in Pakistan.",
        )
        db.add(pke_src1)
        logger.info(f"Registered pke_source: {SOURCE_PUBUNIV_ID}")

    op_src1 = db.query(Source).filter(Source.source_url == SOURCE_PUBUNIV_URL).first()
    if not op_src1:
        op_src1 = Source(
            source_url=SOURCE_PUBUNIV_URL,
            source_name=SOURCE_PUBUNIV_NAME,
            source_type="EXTERNAL_SECONDARY",
            domain="macro_statistics",
            classification="SECONDARY",
            retrieval_method="csv_import",
            retrieved_at=datetime.utcnow(),
            last_verified=datetime.utcnow(),
            verification_status="SECONDARY",
            confidence=0.75,
            notes="External secondary public university time-series.",
        )
        db.add(op_src1)

    # 2. Dataset 2 Source
    pke_src2 = db.query(PKESource).filter(PKESource.source_id == SOURCE_CS_FACULTY_ID).first()
    if not pke_src2:
        pke_src2 = PKESource(
            source_id=SOURCE_CS_FACULTY_ID,
            name=SOURCE_CS_FACULTY_NAME,
            base_url=SOURCE_CS_FACULTY_URL,
            authority_level="L2",
            source_type="EXTERNAL_SECONDARY",
            domains="universities,programs,faculty_intellectual_capital",
            geographic_scope="nationwide",
            access_review_status="APPROVED",
            retrieval_method="csv_import",
            has_official_api=False,
            is_reachable=True,
            source_confidence=75,
            notes="Secondary dataset documenting CS faculty, terminal degrees, and research specializations in Pakistan.",
        )
        db.add(pke_src2)
        logger.info(f"Registered pke_source: {SOURCE_CS_FACULTY_ID}")

    op_src2 = db.query(Source).filter(Source.source_url == SOURCE_CS_FACULTY_URL).first()
    if not op_src2:
        op_src2 = Source(
            source_url=SOURCE_CS_FACULTY_URL,
            source_name=SOURCE_CS_FACULTY_NAME,
            source_type="EXTERNAL_SECONDARY",
            domain="faculty_intellectual_capital",
            classification="SECONDARY",
            retrieval_method="csv_import",
            retrieved_at=datetime.utcnow(),
            last_verified=datetime.utcnow(),
            verification_status="SECONDARY",
            confidence=0.75,
            notes="External secondary Pakistan Intellectual Capital (CS) faculty dataset.",
        )
        db.add(op_src2)

    db.commit()
    db.refresh(pke_src1)
    db.refresh(pke_src2)
    return pke_src1, pke_src2


def import_public_universities_macro_csv(
    db, filepath: Path, source: PKESource, dry_run: bool = False
) -> Dict[str, Any]:
    """
    Import number-of-public-universities-in-pakistan.csv into pke_staging_records.
    Idempotent: Uses dedup_key 'macro_stat:pub_univ:<year>'.
    """
    logger.info(f"Processing Dataset 1: {filepath.name}")
    stats = {
        "filename": filepath.name,
        "rows_found": 0,
        "rows_imported": 0,
        "rows_skipped": 0,
        "rows_rejected": 0,
    }

    # utf-8-sig handles UTF-8 BOM
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = [h.strip().replace("\ufeff", "") for h in (reader.fieldnames or [])]
        expected_fields = {"Year", "Total", "Male", "Female"}
        if not expected_fields.issubset(set(fieldnames)):
            raise ValueError(f"Dataset 1 missing expected columns {expected_fields}. Found: {fieldnames}")

        for raw_row in reader:
            stats["rows_found"] += 1
            year = (raw_row.get("Year") or "").strip()
            total_raw = (raw_row.get("Total") or "").strip()
            male_raw = (raw_row.get("Male") or "").strip()
            female_raw = (raw_row.get("Female") or "").strip()

            # Validation
            if not year or not total_raw:
                stats["rows_rejected"] += 1
                logger.warning(f"Rejecting malformed row in {filepath.name}: {raw_row}")
                continue

            try:
                total = int(total_raw)
                male = int(male_raw) if male_raw else None
                female = int(female_raw) if female_raw else None
            except ValueError:
                stats["rows_rejected"] += 1
                logger.warning(f"Rejecting row with invalid numeric values in {filepath.name}: {raw_row}")
                continue

            dedup_key = f"macro_stat:pub_univ:{year}"
            content_hash = hashlib.sha256(f"{year}:{total}:{male}:{female}".encode()).hexdigest()

            # Check if record already staged
            existing = (
                db.query(PKEStagingRecord)
                .filter(PKEStagingRecord.dedup_key == dedup_key)
                .first()
            )
            if existing:
                stats["rows_skipped"] += 1
                continue

            payload = {
                "year": year,
                "total_public_universities": total,
                "male_or_coed_institutions": male,
                "female_only_institutions": female,
                "metric_type": "public_university_count",
                "authority_level": "L2",
                "source_type": "EXTERNAL_SECONDARY",
                "provenance": {
                    "source_id": source.source_id,
                    "source_name": source.name,
                    "dataset_file": filepath.name,
                    "imported_at": datetime.utcnow().isoformat(),
                },
            }

            if not dry_run:
                staging_rec = PKEStagingRecord(
                    domain="macro_statistics",
                    extracted_json=json.dumps(payload),
                    source_url=source.base_url,
                    source_id=source.id,
                    content_hash=content_hash,
                    dedup_key=dedup_key,
                    verification_status="SECONDARY",
                )
                db.add(staging_rec)
            stats["rows_imported"] += 1

    if not dry_run:
        db.commit()
    logger.info(f"Dataset 1 completed: {stats}")
    return stats


def import_cs_intellectual_capital_csv(
    db, filepath: Path, source: PKESource, dry_run: bool = False
) -> Dict[str, Any]:
    """
    Import pakistan-intellectual-capital-computer-science-ver-1.csv.
    - Validates faculty rows.
    - Stages faculty records under 'faculty_intellectual_capital'.
    - Matches universities against primary PKE institutions without overwriting primary data.
    - Stages unverified universities under 'university_candidates'.
    - Computes and stages secondary intellectual capital enrichments for primary universities.
    """
    logger.info(f"Processing Dataset 2: {filepath.name}")
    stats = {
        "filename": filepath.name,
        "rows_found": 0,
        "rows_imported": 0,
        "rows_skipped": 0,
        "rows_rejected": 0,
        "matched_primary_universities": 0,
        "unmatched_universities_staged": 0,
        "enrichment_records_staged": 0,
    }

    # Load existing primary verified universities
    primary_unis = db.query(University).all()
    primary_by_slug = {u.slug: u for u in primary_unis}
    primary_by_norm_name = {normalize_text(u.name): u for u in primary_unis}
    for u in primary_unis:
        if u.short_name:
            primary_by_norm_name[normalize_text(u.short_name)] = u

    # Aggregators by matched primary university ID
    matched_univ_faculty: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    unmatched_univ_records: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # Read latin1 encoding safely
    with open(filepath, "r", encoding="latin1", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        required = {"Teacher Name", "University Currently Teaching", "Department"}
        if not required.issubset(fieldnames):
            raise ValueError(f"Dataset 2 missing required fields {required}. Found: {fieldnames}")

        for raw_row in reader:
            stats["rows_found"] += 1
            teacher_name = (raw_row.get("Teacher Name") or "").strip()
            univ_name = (raw_row.get("University Currently Teaching") or "").strip()
            dept = (raw_row.get("Department") or "").strip()
            province = (raw_row.get("Province University Located") or "").strip()
            designation = (raw_row.get("Designation") or "").strip()
            terminal_degree = (raw_row.get("Terminal Degree") or "").strip()
            grad_from = (raw_row.get("Graduated from") or "").strip()
            country = (raw_row.get("Country") or "").strip()
            year = (raw_row.get("Year") or "").strip()
            specialization = (raw_row.get("Area of Specialization/Research Interests") or "").strip()

            # Validation
            if not teacher_name or not univ_name:
                stats["rows_rejected"] += 1
                continue

            # Deduplication key for faculty record
            faculty_hash = hashlib.sha256(
                f"{teacher_name}|{univ_name}|{dept}|{designation}|{terminal_degree}".encode()
            ).hexdigest()
            dedup_key = f"cs_faculty:{faculty_hash[:32]}"

            existing = (
                db.query(PKEStagingRecord)
                .filter(PKEStagingRecord.dedup_key == dedup_key)
                .first()
            )
            if existing:
                stats["rows_skipped"] += 1
            else:
                faculty_payload = {
                    "teacher_name": teacher_name,
                    "university_name": univ_name,
                    "department": dept,
                    "province": province,
                    "designation": designation,
                    "terminal_degree": terminal_degree,
                    "graduated_from": grad_from,
                    "country": country,
                    "graduation_year": year,
                    "specialization": specialization,
                    "authority_level": "L2",
                    "source_type": "EXTERNAL_SECONDARY",
                    "provenance": {
                        "source_id": source.source_id,
                        "source_name": source.name,
                        "dataset_file": filepath.name,
                    },
                }

                if not dry_run:
                    staging_rec = PKEStagingRecord(
                        domain="faculty_intellectual_capital",
                        extracted_json=json.dumps(faculty_payload),
                        source_url=source.base_url,
                        source_id=source.id,
                        content_hash=faculty_hash,
                        dedup_key=dedup_key,
                        verification_status="SECONDARY",
                    )
                    db.add(staging_rec)
                stats["rows_imported"] += 1

            # Match against primary PKE institutions
            norm_u = normalize_text(univ_name)
            matched_uni = None

            # 1. Exact or partial match on primary name / short_name
            if norm_u in primary_by_norm_name:
                matched_uni = primary_by_norm_name[norm_u]
            elif norm_u in UNIVERSITY_ALIASES:
                slug = UNIVERSITY_ALIASES[norm_u]
                matched_uni = primary_by_slug.get(slug)
            else:
                for p_norm, u_obj in primary_by_norm_name.items():
                    if len(norm_u) > 3 and (norm_u == p_norm or norm_u in p_norm or p_norm in norm_u):
                        matched_uni = u_obj
                        break

            item_data = {
                "teacher_name": teacher_name,
                "department": dept,
                "designation": designation,
                "terminal_degree": terminal_degree,
                "specialization": specialization,
                "province": province,
            }

            if matched_uni:
                matched_univ_faculty[matched_uni.id].append(item_data)
            else:
                unmatched_univ_records[univ_name].append(item_data)

    stats["matched_primary_universities"] = len(matched_univ_faculty)
    logger.info(
        f"Matched {len(matched_univ_faculty)} primary universities. "
        f"Found {len(unmatched_univ_records)} unverified candidate universities."
    )

    # 1. Stage unmatched universities as candidate records (NEEDS_REVIEW)
    for u_raw_name, fac_list in unmatched_univ_records.items():
        cand_key = f"candidate_uni:{hashlib.sha256(u_raw_name.strip().lower().encode()).hexdigest()[:24]}"
        existing_cand = (
            db.query(PKEStagingRecord)
            .filter(PKEStagingRecord.dedup_key == cand_key)
            .first()
        )
        if not existing_cand and not dry_run:
            cand_payload = {
                "name": u_raw_name,
                "faculty_count": len(fac_list),
                "provinces": list({f["province"] for f in fac_list if f["province"]}),
                "departments": list({f["department"] for f in fac_list if f["department"]}),
                "review_status": "NEEDS_REVIEW",
                "authority_level": "L2",
                "source_type": "EXTERNAL_SECONDARY",
                "notes": "Unmatched university from external secondary faculty dataset. Not visible to students.",
            }
            cand_rec = PKEStagingRecord(
                domain="university_candidates",
                extracted_json=json.dumps(cand_payload),
                source_url=source.base_url,
                source_id=source.id,
                content_hash=hashlib.sha256(u_raw_name.encode()).hexdigest(),
                dedup_key=cand_key,
                verification_status="CANDIDATE",
            )
            db.add(cand_rec)
            stats["unmatched_universities_staged"] += 1

    # 2. Stage secondary intellectual capital enrichment for matched primary universities
    # PRIMARY DATA WINS: University table fields are NEVER altered.
    for uni_id, fac_list in matched_univ_faculty.items():
        uni = db.query(University).filter(University.id == uni_id).first()
        if not uni:
            continue

        phd_count = sum(1 for f in fac_list if "phd" in f.get("terminal_degree", "").lower())
        dept_counts = Counter(f["department"] for f in fac_list if f.get("department"))
        specs = []
        for f in fac_list:
            spec_str = f.get("specialization") or ""
            for s in spec_str.split(","):
                s_clean = s.strip()
                if len(s_clean) > 2:
                    specs.append(s_clean)
        top_specs = [s for s, _ in Counter(specs).most_common(12)]

        enrich_key = f"enrichment:university:{uni.id}"
        enrich_payload = {
            "university_id": uni.id,
            "university_name": uni.name,
            "university_slug": uni.slug,
            "cs_faculty_count": len(fac_list),
            "phd_faculty_count": phd_count,
            "departments": list(dept_counts.keys()),
            "top_specializations": top_specs,
            "sample_faculty": [
                {
                    "name": f["teacher_name"],
                    "designation": f["designation"],
                    "degree": f["terminal_degree"],
                }
                for f in fac_list[:5]
            ],
            "authority_level": "L2",
            "source_type": "EXTERNAL_SECONDARY",
            "is_primary": False,
            "provenance": {
                "source_id": source.source_id,
                "source_name": source.name,
                "dataset_file": filepath.name,
                "updated_at": datetime.utcnow().isoformat(),
            },
        }

        enrich_json = json.dumps(enrich_payload)
        content_hash = hashlib.sha256(enrich_json.encode()).hexdigest()

        existing_enrich = (
            db.query(PKEStagingRecord)
            .filter(PKEStagingRecord.dedup_key == enrich_key)
            .first()
        )

        if existing_enrich:
            # Update existing staged enrichment payload without touching primary university
            if not dry_run:
                existing_enrich.extracted_json = enrich_json
                existing_enrich.content_hash = content_hash
        else:
            if not dry_run:
                staged_enrich = PKEStagingRecord(
                    domain="university_secondary_enrichment",
                    extracted_json=enrich_json,
                    source_url=source.base_url,
                    source_id=source.id,
                    content_hash=content_hash,
                    dedup_key=enrich_key,
                    verification_status="SECONDARY",
                )
                db.add(staged_enrich)
            stats["enrichment_records_staged"] += 1

    if not dry_run:
        db.commit()

    logger.info(f"Dataset 2 completed: {stats}")
    return stats


def run_import(dry_run: bool = False) -> Dict[str, Any]:
    """Execute complete import of both secondary external datasets."""
    init_db()
    db = SessionLocal()
    try:
        # 1. Register sources
        pke_src1, pke_src2 = register_pke_sources(db)

        # 2. Dataset 1: Public universities historical count
        f1_path = find_dataset_path("number-of-public-universities-in-pakistan.csv")
        ds1_stats = import_public_universities_macro_csv(db, f1_path, pke_src1, dry_run=dry_run)

        # 3. Dataset 2: Pakistan intellectual capital (CS faculty)
        f2_path = find_dataset_path("pakistan-intellectual-capital-computer-science-ver-1.csv")
        ds2_stats = import_cs_intellectual_capital_csv(db, f2_path, pke_src2, dry_run=dry_run)

        summary = {
            "dataset_1": ds1_stats,
            "dataset_2": ds2_stats,
            "dry_run": dry_run,
        }
        return summary
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import external secondary CSV datasets into Career OS PKE.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and parse without committing to DB")
    args = parser.parse_args()

    res = run_import(dry_run=args.dry_run)
    print("\n" + "=" * 50)
    print("IMPORT SUMMARY REPORT:")
    print("=" * 50)
    print(json.dumps(res, indent=2))
