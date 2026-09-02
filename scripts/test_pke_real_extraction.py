"""
Pakistan Knowledge Engine — Real Extraction Test Script (Step 3).

This script performs a LIVE extraction test on 4 approved sources using
the newly added PKE domains, schemas, and prompts.

Usage (from repository root):
    python scripts/test_pke_real_extraction.py
"""

import sys
import os
from pathlib import Path
from pprint import pprint

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "BackEnd"))

from database import SessionLocal, init_db
from ingestion.ingestion_service import run_url_ingestion, get_run_status
from knowledge_engine.staging import PKEStagingRecord
from models.opportunity import Opportunity
from config import settings


def main():
    print("Initializing Database...")
    init_db()
    db = SessionLocal()

    if not settings.DASHSCOPE_API_KEY:
        print("WARNING: DASHSCOPE_API_KEY not set. Extraction will use fallback/mock responses if AI is disabled.")
    
    # 4 sources mapped to 4 domains
    test_cases = [
        {
            "domain": "universities",
            "url": "https://www.iba.edu.pk",
            "source_type": "OFFICIAL_UNIVERSITY"
        },
        {
            "domain": "learning_resources",
            "url": "https://www.digiskills.pk",
            "source_type": "OFFICIAL_GOVERNMENT"
        },
        {
            "domain": "schools",
            "url": "https://fde.gov.pk",
            "source_type": "OFFICIAL_GOVERNMENT"
        },
        {
            "domain": "sports",
            "url": "https://www.pcb.com.pk",
            "source_type": "OFFICIAL_SPORTS"
        }
    ]

    print("\n--- Starting Real Extraction Test ---\n")

    for tc in test_cases:
        domain = tc["domain"]
        url = tc["url"]
        stype = tc["source_type"]
        
        print(f"Testing domain: {domain.upper()} | URL: {url}")
        
        try:
            result = run_url_ingestion(db, urls=[url], source_type=stype, domain=domain, run_label=f"test_{domain}")
            run_id = result["run_id"]
            
            # Wait/check status (synchronous so it's already done)
            status = get_run_status(db, run_id)
            print(f"  -> Run Status: {status['status']} | Successful: {status['successful_items']} | Failed: {status['failed_items']}")
            
            for item in status["items"]:
                if item["status"] == "FAILED":
                    print(f"  -> ERROR: {item['error_message']}")
                elif item["status"] in ("STORED", "DUPLICATE"):
                    print(f"  -> Successfully processed item ({item['status']}).")
                    
                    if domain in ["scholarships", "jobs", "internships", "programs"]:
                        opp = db.query(Opportunity).filter(Opportunity.id == item["opportunity_id"]).first()
                        if opp:
                            print(f"  -> Created Opportunity: {opp.title} [Status: {opp.verification_status}]")
                    else:
                        # Find the staging record
                        stg = db.query(PKEStagingRecord).filter(PKEStagingRecord.source_url == item["source_url"]).order_by(PKEStagingRecord.id.desc()).first()
                        if stg:
                            print(f"  -> Created StagingRecord [Status: {stg.verification_status}]")
                            print("  -> Extracted JSON:")
                            pprint(stg.extracted_json)
                            
        except Exception as e:
            print(f"  -> FATAL EXCEPTION: {e}")
            
        print("-" * 40)

    db.close()
    print("Real Extraction Test Complete.")


if __name__ == "__main__":
    main()
