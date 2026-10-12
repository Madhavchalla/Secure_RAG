import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models.user import User
from app.models.document import Document, DocumentPermission, DocumentChunk
from app.models.audit import RiskAssessment, AuditLog, SecurityEvent


def test_core_setup():
    print("[1/5] Testing environment settings...")
    assert settings.APP_NAME == "RAS-RAG"
    assert settings.THRESHOLD_ALLOW == 30.0
    print("  -> Settings loaded successfully.")

    print("[2/5] Testing password hashing and JWT...")
    raw_pass = "TestPassword@123"
    hashed = hash_password(raw_pass)
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

    token = create_access_token({"sub": "1", "username": "admin", "role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["username"] == "admin"
    assert payload["role"] == "admin"
    print("  -> Cryptography, bcrypt, and JWT operations verified.")

    print("[3/5] Initializing SQLite database schema...")
    Base.metadata.create_all(bind=engine)
    print("  -> Tables created successfully in SQLite.")

    print("[4/5] Testing transactional DB session & User seeding...")
    db = SessionLocal()
    try:
        # Check or create test admin
        test_user = db.query(User).filter(User.username == "admin_test").first()
        if not test_user:
            test_user = User(
                username="admin_test",
                email="admin_test@rasrag.local",
                hashed_password=hash_password("AdminSecure@2026"),
                role="admin",
                is_active=True,
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        assert test_user.id is not None
        assert test_user.role == "admin"
        print(f"  -> User verified: ID={test_user.id}, Username={test_user.username}")

        # Test Audit log creation
        audit = AuditLog(
            user_id=test_user.id,
            action="SYSTEM_INIT_TEST",
            resource_type="SYSTEM",
            status="SUCCESS",
            ip_address="127.0.0.1",
        )
        db.add(audit)
        db.commit()
        assert audit.id is not None
        print(f"  -> Audit log verified: ID={audit.id}, Action={audit.action}")

    finally:
        db.close()

    print("[5/5] Testing heavy library imports (PyMuPDF, docx, chromadb, sentence_transformers)...")
    import fitz  # PyMuPDF
    import docx
    import chromadb
    import sentence_transformers

    print(f"  -> PyMuPDF version: {fitz.__version__}")
    print(f"  -> python-docx imported successfully")
    print(f"  -> ChromaDB version: {chromadb.__version__}")
    print(f"  -> sentence-transformers version: {sentence_transformers.__version__}")

    print("\n[SUCCESS] ALL CORE BACKEND FOUNDATIONS VERIFIED 100%!")


if __name__ == "__main__":
    test_core_setup()
