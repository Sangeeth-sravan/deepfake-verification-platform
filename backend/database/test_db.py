import sys
import os
import uuid

# Ensure backend root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import engine, SessionLocal, Base
from database.models import VerificationRecord

def run_db_tests():
    print("=== STARTING DATABASE VERIFICATION TEST ===")
    
    # 1. Ensure tables are created
    Base.metadata.create_all(bind=engine)
    print("[PASS] SQLite database tables created/verified successfully.")

    db = SessionLocal()
    test_id = f"TEST-{uuid.uuid4().hex[:6].upper()}"

    try:
        # 2. Insert test record
        record = VerificationRecord(
            verification_id=test_id,
            verification_type="TEST",
            result="VERIFIED",
            confidence=0.99,
            risk_score=5,
            risk_level="LOW",
            filename="sample_test.png",
            details='{"test": true, "note": "temporary record"}'
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        print(f"[PASS] Temporary VerificationRecord inserted (ID: {record.id}, Code: {record.verification_id}).")

        # 3. Query record
        queried = db.query(VerificationRecord).filter_by(verification_id=test_id).first()
        assert queried is not None, "Failed to query inserted record"
        assert queried.confidence == 0.99, "Confidence score mismatch"
        assert queried.risk_score == 5, "Risk score mismatch"
        print(f"[PASS] Record queried successfully: {queried}")

        # 4. Clean up test record (remove so DB remains clean)
        db.delete(queried)
        db.commit()
        print(f"[PASS] Test record {test_id} cleaned up successfully from database.")

    except Exception as e:
        db.rollback()
        print(f"[FAIL] Database test encountered an error: {e}")
        sys.exit(1)
    finally:
        db.close()
        print("[PASS] Database session closed cleanly.")

    print("=== ALL DATABASE TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_db_tests()
