"""Smoke test for the submission-critical image API flow.

Run from backend: .\\venv\\Scripts\\python.exe test_api_integration.py
"""
import io
import os
import sys

from PIL import Image
from fastapi.testclient import TestClient

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


def make_image() -> bytes:
    image = Image.new("RGB", (96, 96), color=(30, 140, 220))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()


def run_api_smoke_test():
    verification_id = None
    client = TestClient(app)
    try:
        with client:
            health = client.get("/api/health")
            assert health.status_code == 200, health.text

            response = client.post(
                "/api/image/analyze",
                files={"file": ("sample.jpg", make_image(), "image/jpeg")},
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            verification_id = payload["verification_id"]
            assert payload["verification_type"] == "IMAGE"

            history = client.get("/api/history")
            assert history.status_code == 200, history.text
            assert any(item["verification_id"] == verification_id for item in history.json()["history"])

            details = client.get(f"/api/history/{verification_id}")
            assert details.status_code == 200, details.text
            assert details.json()["forensics"] is not None

            report = client.get(f"/api/report/{verification_id}/download")
            assert report.status_code == 200, report.text
            assert report.headers["content-type"].startswith("application/pdf")
            assert report.content.startswith(b"%PDF-")
        print("[PASS] Image upload, SQLite history, details, and PDF report flow works.")
    finally:
        if verification_id:
            db = SessionLocal()
            try:
                record = db.query(VerificationRecord).filter_by(verification_id=verification_id).first()
                if record:
                    db.delete(record)
                    db.commit()
            finally:
                db.close()
            upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "images"))
            for filename in os.listdir(upload_dir):
                if filename.startswith(verification_id):
                    os.remove(os.path.join(upload_dir, filename))


if __name__ == "__main__":
    run_api_smoke_test()


def test_api_smoke():
    run_api_smoke_test()
