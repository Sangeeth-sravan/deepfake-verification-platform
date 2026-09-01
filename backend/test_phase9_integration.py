"""
Phase 9 – Dashboard & Integration Smoke Test
=============================================
Tests:
  1. /api/health
  2. /api/stats  – returns correct per-type and per-risk-level counts
  3. /api/history – filtering by type, filtering by risk_level
  4. End-to-end image → history → details → PDF
  5. End-to-end audio → history → details → PDF  (reuses Phase 7 WAV generator)
  6. /api/report for a DIGITAL_IDENTITY record (created in test 7 of Phase 8)
  7. Stats totals update after a new scan

Run from backend directory:
    .\\venv\\Scripts\\python.exe test_phase9_integration.py
"""

import io
import math
import os
import sys
import wave

import cv2
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

# --------------------------------------------------------------------------
# Path setup – identical to other tests
# --------------------------------------------------------------------------
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

client = TestClient(app)

# --------------------------------------------------------------------------
# Synthetic media generators
# --------------------------------------------------------------------------

def make_jpeg() -> bytes:
    img = Image.new("RGB", (120, 120), color=(40, 160, 220))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def make_wav(duration: float = 1.0, sample_rate: int = 16000) -> bytes:
    t = np.arange(int(sample_rate * duration)) / sample_rate
    samples = (0.35 * np.sin(2 * math.pi * 440 * t) + 0.03 * np.sin(2 * math.pi * 1800 * t))
    pcm = np.clip(samples * 32767, -32768, 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def make_id_doc() -> bytes:
    img = np.full((300, 480, 3), (30, 30, 60), dtype=np.uint8)
    cv2.rectangle(img, (8, 8), (472, 292), (80, 80, 160), 3)
    cv2.ellipse(img, (75, 90), (45, 55), 0, 0, 360, (200, 180, 150), -1)
    cv2.putText(img, "NATIONAL ID", (140, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 255), 1)
    buf = io.BytesIO()
    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def make_selfie() -> bytes:
    img = np.full((400, 320, 3), (20, 15, 25), dtype=np.uint8)
    noise = np.random.randint(0, 30, img.shape, dtype=np.uint8)
    img = cv2.add(img, noise)
    cv2.ellipse(img, (160, 180), (90, 110), 0, 0, 360, (200, 170, 140), -1)
    face = img[70:290, 70:250]
    fn = np.random.normal(0, 12, face.shape).astype(np.int16)
    img[70:290, 70:250] = np.clip(face.astype(np.int16) + fn, 0, 255).astype(np.uint8)
    cv2.circle(img, (130, 155), 14, (60, 40, 30), -1)
    cv2.circle(img, (190, 155), 14, (60, 40, 30), -1)
    buf = io.BytesIO()
    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# --------------------------------------------------------------------------
# Cleanup helper
# --------------------------------------------------------------------------

def cleanup_db(verification_ids: list[str]) -> None:
    db = SessionLocal()
    try:
        for vid in verification_ids:
            rec = db.query(VerificationRecord).filter_by(verification_id=vid).first()
            if rec:
                db.delete(rec)
        db.commit()
    finally:
        db.close()

    # Remove uploaded files created by these tests
    for subdir in ("images", "audio", "identity"):
        udir = os.path.abspath(os.path.join(backend_root, "..", "uploads", subdir))
        if os.path.isdir(udir):
            for fname in os.listdir(udir):
                if any(fname.startswith(vid) for vid in verification_ids):
                    try:
                        os.remove(os.path.join(udir, fname))
                    except OSError:
                        pass


# --------------------------------------------------------------------------
# Test runner
# --------------------------------------------------------------------------

def run_phase9_smoke_test():
    print("=== PHASE 9 DASHBOARD & INTEGRATION SMOKE TEST ===")
    created_ids: list[str] = []

    with client:

        # ------------------------------------------------------------------
        # Test 1: Health check
        # ------------------------------------------------------------------
        r = client.get("/api/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        assert r.json()["status"] == "healthy"
        assert r.json()["database"] == "connected"
        print("[PASS] Test 1: /api/health returns healthy + db connected.")

        # ------------------------------------------------------------------
        # Test 2: Stats endpoint structure
        # ------------------------------------------------------------------
        r = client.get("/api/stats")
        assert r.status_code == 200, f"Stats failed: {r.text}"
        stats = r.json()
        assert "by_type" in stats, "Missing by_type in stats"
        assert "by_risk_level" in stats, "Missing by_risk_level in stats"
        for key in ("IMAGE", "VIDEO", "AUDIO", "DIGITAL_IDENTITY"):
            assert key in stats["by_type"], f"Missing {key} in by_type"
        print(f"[PASS] Test 2: /api/stats returns correct structure. "
              f"Current totals: {stats['by_type']}")

        # ------------------------------------------------------------------
        # Test 3: History – risk_level filter
        # ------------------------------------------------------------------
        r_low = client.get("/api/history", params={"risk_level": "LOW", "limit": 5})
        assert r_low.status_code == 200, r_low.text
        for item in r_low.json()["history"]:
            assert item["risk_level"] == "LOW", f"Unexpected risk_level: {item['risk_level']}"
        print("[PASS] Test 3: /api/history?risk_level=LOW filters correctly.")

        # ------------------------------------------------------------------
        # Test 4: New IMAGE scan → stats update
        # ------------------------------------------------------------------
        stats_before = client.get("/api/stats").json()
        img_count_before = stats_before["by_type"].get("IMAGE", 0)

        r = client.post(
            "/api/image/analyze",
            files={"file": ("phase9_test.jpg", make_jpeg(), "image/jpeg")},
        )
        assert r.status_code == 200, f"Image analyze failed: {r.text}"
        img_vid = r.json()["verification_id"]
        created_ids.append(img_vid)
        assert img_vid.startswith("IMG-")
        assert r.json()["verification_type"] == "IMAGE"

        stats_after = client.get("/api/stats").json()
        assert stats_after["by_type"]["IMAGE"] == img_count_before + 1, \
            f"IMAGE count did not increment: {stats_after['by_type']['IMAGE']} vs {img_count_before + 1}"
        print(f"[PASS] Test 4: Image scan created ({img_vid}), stats incremented correctly.")

        # ------------------------------------------------------------------
        # Test 5: IMAGE → history → details → PDF
        # ------------------------------------------------------------------
        hist = client.get("/api/history", params={"verification_type": "IMAGE"})
        assert hist.status_code == 200
        ids_in_hist = [h["verification_id"] for h in hist.json()["history"]]
        assert img_vid in ids_in_hist, f"{img_vid} not found in image history"

        det = client.get(f"/api/history/{img_vid}")
        assert det.status_code == 200
        assert det.json()["forensics"]["ela_score"] is not None
        assert isinstance(det.json()["detected_issues"], list)

        pdf = client.get(f"/api/report/{img_vid}/download")
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF-")
        assert b"IMAGE" in pdf.content
        assert b"ELA Score" in pdf.content, "PDF missing forensic ELA line"
        print(f"[PASS] Test 5: IMAGE -> history -> details -> PDF all valid.")

        # ------------------------------------------------------------------
        # Test 6: AUDIO → history → details → PDF
        # ------------------------------------------------------------------
        r = client.post(
            "/api/audio/analyze",
            files={"file": ("phase9_test.wav", make_wav(), "audio/wav")},
        )
        assert r.status_code == 200, f"Audio analyze failed: {r.text}"
        aud_vid = r.json()["verification_id"]
        created_ids.append(aud_vid)
        assert aud_vid.startswith("AUD-")

        aud_det = client.get(f"/api/history/{aud_vid}")
        assert aud_det.status_code == 200
        assert aud_det.json()["forensics"]["sample_rate_hz"] == 16000

        aud_pdf = client.get(f"/api/report/{aud_vid}/download")
        assert aud_pdf.status_code == 200
        assert aud_pdf.content.startswith(b"%PDF-")
        assert b"Sample Rate" in aud_pdf.content, "PDF missing AUDIO forensic lines"
        print(f"[PASS] Test 6: AUDIO -> history -> details -> PDF all valid.")

        # ------------------------------------------------------------------
        # Test 7: DIGITAL_IDENTITY → history → details → PDF
        # ------------------------------------------------------------------
        r = client.post(
            "/api/identity/verify",
            files={
                "id_document": ("p9_id.jpg", make_id_doc(), "image/jpeg"),
                "selfie": ("p9_selfie.jpg", make_selfie(), "image/jpeg"),
            },
        )
        assert r.status_code == 200, f"Identity verify failed: {r.text}"
        idv_vid = r.json()["verification_id"]
        created_ids.append(idv_vid)
        assert idv_vid.startswith("IDV-")

        idv_det = client.get(f"/api/history/{idv_vid}")
        assert idv_det.status_code == 200
        assert idv_det.json()["forensics"]["id_ela_score"] is not None
        assert "selfie_liveness_passed" in idv_det.json()["forensics"]

        idv_pdf = client.get(f"/api/report/{idv_vid}/download")
        assert idv_pdf.status_code == 200
        assert idv_pdf.content.startswith(b"%PDF-")
        assert b"Liveness Check" in idv_pdf.content, "PDF missing IDENTITY forensic lines"
        print(f"[PASS] Test 7: DIGITAL_IDENTITY -> history -> details -> PDF all valid.")

        # ------------------------------------------------------------------
        # Test 8: 404 for non-existent record
        # ------------------------------------------------------------------
        r404 = client.get("/api/history/IDV-NONEXISTENT")
        assert r404.status_code == 404, f"Expected 404, got {r404.status_code}"
        r404_pdf = client.get("/api/report/IDV-NONEXISTENT/download")
        assert r404_pdf.status_code == 404, f"Expected 404 PDF, got {r404_pdf.status_code}"
        print("[PASS] Test 8: Non-existent IDs return 404 on both history and PDF routes.")

        # ------------------------------------------------------------------
        # Test 9: Stats by_type sums correctly
        # ------------------------------------------------------------------
        final_stats = client.get("/api/stats").json()
        total_from_types = sum(final_stats["by_type"].values())
        total_from_risk  = sum(final_stats["by_risk_level"].values())
        assert total_from_types == total_from_risk, \
            f"Stats mismatch: by_type sum={total_from_types}, by_risk_level sum={total_from_risk}"
        print(f"[PASS] Test 9: Stats totals consistent (total={total_from_types}).")

    print("=== ALL PHASE 9 SMOKE TESTS PASSED ===")

    # Cleanup test records
    cleanup_db(created_ids)
    print(f"[INFO] Cleaned up {len(created_ids)} test records from database.")


if __name__ == "__main__":
    run_phase9_smoke_test()


def test_phase9_smoke():
    run_phase9_smoke_test()
