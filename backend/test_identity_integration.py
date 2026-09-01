"""Smoke test for the Phase 8 Digital Identity Verification endpoint.

Tests the full request/persistence/history/PDF flow using synthetic JPEG images
so no real ID documents or selfies are required.

Run from the backend directory:
    .\\venv\\Scripts\\python.exe test_identity_integration.py
"""

import io
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Path setup – identical to the other integration tests
# ---------------------------------------------------------------------------
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_root = os.path.abspath(os.path.dirname(__file__))
for path in (workspace_root, backend_root):
    if path in sys.path:
        sys.path.remove(path)
sys.path.insert(0, workspace_root)
sys.path.insert(1, backend_root)

from main import app
from database.connection import SessionLocal
from database.models import VerificationRecord


# ---------------------------------------------------------------------------
# Image generators
# ---------------------------------------------------------------------------

def make_id_document_image() -> bytes:
    """
    Generates a synthetic 'ID document' image:
    - Rectangular card with a coloured rectangle simulating a document
    - An oval 'face photo' region in the top-left
    - Text placeholders to mimic printed text lines
    """
    img = np.full((300, 480, 3), (30, 30, 60), dtype=np.uint8)
    # Document border
    cv2.rectangle(img, (8, 8), (472, 292), (80, 80, 160), 3)
    # Simulated face box (top-left quadrant)
    cv2.rectangle(img, (20, 20), (130, 160), (60, 100, 180), -1)
    cv2.ellipse(img, (75, 90), (45, 55), 0, 0, 360, (200, 180, 150), -1)
    # Simulated text lines
    for row_y in range(180, 290, 22):
        cv2.rectangle(img, (150, row_y), (460, row_y + 14), (50, 50, 90), -1)
    # Issuing authority text
    cv2.putText(img, "NATIONAL ID CARD", (140, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 255), 1)
    buf = io.BytesIO()
    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def make_selfie_image() -> bytes:
    """
    Generates a synthetic selfie with an oval face, eyes, and textured skin to
    allow Haar cascade to detect a face and pass the liveness texture check.
    """
    img = np.full((400, 320, 3), (20, 15, 25), dtype=np.uint8)
    # Background gradient (texture)
    noise = np.random.randint(0, 30, img.shape, dtype=np.uint8)
    img = cv2.add(img, noise)
    # Skin-tone face oval
    cv2.ellipse(img, (160, 180), (90, 110), 0, 0, 360, (200, 170, 140), -1)
    # Add Gaussian noise to the face region for texture (helps liveness check)
    face_region = img[70:290, 70:250]
    face_noise = np.random.normal(0, 12, face_region.shape).astype(np.int16)
    face_region = np.clip(face_region.astype(np.int16) + face_noise, 0, 255).astype(np.uint8)
    img[70:290, 70:250] = face_region
    # Eyes
    cv2.circle(img, (130, 155), 14, (60, 40, 30), -1)
    cv2.circle(img, (190, 155), 14, (60, 40, 30), -1)
    cv2.circle(img, (130, 155), 6, (230, 220, 210), -1)
    cv2.circle(img, (190, 155), 6, (230, 220, 210), -1)
    # Nose and mouth
    cv2.ellipse(img, (160, 195), (12, 8), 0, 0, 180, (160, 130, 110), 2)
    cv2.ellipse(img, (160, 225), (22, 10), 0, 0, 180, (140, 80, 80), 2)
    buf = io.BytesIO()
    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(buf, format="JPEG", quality=92)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_identity_smoke_test():
    print("=== PHASE 8 DIGITAL IDENTITY VERIFICATION SMOKE TEST ===")
    verification_id = None
    client = TestClient(app)

    try:
        with client:
            # ------------------------------------------------------------------
            # Test 1: Missing files → 422
            # ------------------------------------------------------------------
            resp = client.post("/api/identity/verify")
            assert resp.status_code == 422, f"Expected 422 for missing files, got {resp.status_code}: {resp.text}"
            print("[PASS] Test 1: Missing files returns 422 Unprocessable Entity.")

            # ------------------------------------------------------------------
            # Test 2: Wrong file type → 400
            # ------------------------------------------------------------------
            bad_resp = client.post(
                "/api/identity/verify",
                files={
                    "id_document": ("id.txt", b"not an image", "text/plain"),
                    "selfie": ("selfie.jpg", make_selfie_image(), "image/jpeg"),
                },
            )
            assert bad_resp.status_code == 400, (
                f"Expected 400 for bad file type, got {bad_resp.status_code}: {bad_resp.text}"
            )
            print("[PASS] Test 2: Non-image ID document returns 400 Bad Request.")

            # ------------------------------------------------------------------
            # Test 3: Successful verification
            # ------------------------------------------------------------------
            resp = client.post(
                "/api/identity/verify",
                files={
                    "id_document": ("national_id.jpg", make_id_document_image(), "image/jpeg"),
                    "selfie": ("selfie.jpg", make_selfie_image(), "image/jpeg"),
                },
            )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            payload = resp.json()

            verification_id = payload["verification_id"]
            assert verification_id.startswith("IDV-"), f"Bad verification_id: {verification_id}"
            assert payload["verification_type"] == "DIGITAL_IDENTITY"
            assert payload["result"] in ("VERIFIED", "REQUIRES_REVIEW", "IDENTITY_UNVERIFIED")
            assert 0.0 <= payload["confidence"] <= 1.0
            assert 0 <= payload["risk_score"] <= 100
            assert payload["risk_level"] in ("LOW", "MEDIUM", "HIGH")
            assert isinstance(payload["detected_issues"], list)
            assert len(payload["detected_issues"]) > 0
            assert "explanation" in payload
            forensics = payload["forensics"]
            assert "id_sharpness" in forensics
            assert "selfie_liveness_passed" in forensics
            assert "face_similarity_score" in forensics

            print(
                f"[PASS] Test 3: Identity verification returned result='{payload['result']}', "
                f"confidence={payload['confidence']}, risk_score={payload['risk_score']}, "
                f"risk_level='{payload['risk_level']}'."
            )

            # ------------------------------------------------------------------
            # Test 4: Record persisted → history endpoint
            # ------------------------------------------------------------------
            history = client.get("/api/history", params={"verification_type": "DIGITAL_IDENTITY"})
            assert history.status_code == 200, history.text
            ids = [item["verification_id"] for item in history.json()["history"]]
            assert verification_id in ids, f"{verification_id} not found in history: {ids}"
            print(f"[PASS] Test 4: Record '{verification_id}' appears in /api/history.")

            # ------------------------------------------------------------------
            # Test 5: Details endpoint (includes forensics)
            # ------------------------------------------------------------------
            details = client.get(f"/api/history/{verification_id}")
            assert details.status_code == 200, details.text
            detail_json = details.json()
            assert detail_json["forensics"]["id_sharpness"] is not None
            assert detail_json["forensics"]["selfie_liveness_passed"] is not None
            print(f"[PASS] Test 5: /api/history/{verification_id} returns full forensic details.")

            # ------------------------------------------------------------------
            # Test 6: PDF report
            # ------------------------------------------------------------------
            report = client.get(f"/api/report/{verification_id}/download")
            assert report.status_code == 200, report.text
            assert report.headers["content-type"].startswith("application/pdf")
            assert report.content.startswith(b"%PDF-")
            print(f"[PASS] Test 6: PDF report downloaded for '{verification_id}'.")

    finally:
        # Cleanup DB record
        if verification_id:
            db = SessionLocal()
            try:
                record = db.query(VerificationRecord).filter_by(
                    verification_id=verification_id
                ).first()
                if record:
                    db.delete(record)
                    db.commit()
            finally:
                db.close()

            # Cleanup uploaded files
            upload_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "uploads", "identity")
            )
            if os.path.isdir(upload_dir):
                for fname in os.listdir(upload_dir):
                    if fname.startswith(verification_id):
                        os.remove(os.path.join(upload_dir, fname))

    print("=== ALL PHASE 8 IDENTITY VERIFICATION SMOKE TESTS PASSED ===")


if __name__ == "__main__":
    run_identity_smoke_test()
