import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ingestion.parser import DocumentParser
from app.ingestion.scanner import ingestion_scanner
from app.ingestion.chunker import text_chunker


def test_ingestion_pipeline():
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_docs")

    # 1. Test clean document
    clean_path = os.path.join(docs_dir, "01_leave_and_attendance_policy.txt")
    assert os.path.exists(clean_path), f"File missing: {clean_path}"

    pages_clean = DocumentParser.extract_document(clean_path, "01_leave_and_attendance_policy.txt")
    full_text_clean = " ".join([p["text"] for p in pages_clean])
    scan_clean = ingestion_scanner.scan_text(full_text_clean)
    chunks_clean = text_chunker.chunk_pages(pages_clean)

    print("[TEST 1: CLEAN DOC]")
    print(f"  Pages extracted: {len(pages_clean)}")
    print(f"  Chunks generated: {len(chunks_clean)}")
    print(f"  Is suspicious: {scan_clean['is_suspicious']}")
    print(f"  Threat score: {scan_clean['threat_score']}")
    assert scan_clean["is_suspicious"] is False
    assert scan_clean["threat_score"] == 0.0
    assert len(chunks_clean) > 0
    print("  -> Clean document test PASSED!")

    # 2. Test malicious injection document
    malicious_path = os.path.join(docs_dir, "06_malicious_prompt_injection_test.txt")
    assert os.path.exists(malicious_path), f"File missing: {malicious_path}"

    pages_malicious = DocumentParser.extract_document(malicious_path, "06_malicious_prompt_injection_test.txt")
    full_text_malicious = " ".join([p["text"] for p in pages_malicious])
    scan_malicious = ingestion_scanner.scan_text(full_text_malicious)

    print("\n[TEST 2: MALICIOUS INJECTION DOC]")
    print(f"  Is suspicious: {scan_malicious['is_suspicious']}")
    print(f"  Highest severity: {scan_malicious['highest_severity']}")
    print(f"  Threat score: {scan_malicious['threat_score']}")
    print(f"  Triggered rules ({len(scan_malicious['triggered_rules'])}):")
    for r in scan_malicious["triggered_rules"]:
        print(f"    * [{r['id']}] {r['name']} ({r['severity']}): '{r['matched_snippet']}'")

    assert scan_malicious["is_suspicious"] is True
    assert scan_malicious["highest_severity"] == "CRITICAL"
    assert scan_malicious["threat_score"] >= 80.0
    print("  -> Malicious injection quarantine test PASSED!")

    print("\n[SUCCESS] ALL INGESTION & THREAT SCANNER TESTS PASSED 100%!")


if __name__ == "__main__":
    test_ingestion_pipeline()
