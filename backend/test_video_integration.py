"""Smoke test for the video upload and persistence flow."""
import os
import sys
import tempfile

import cv2
import numpy as np
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


def make_video() -> bytes:
    temporary = tempfile.NamedTemporaryFile(suffix=".avi", delete=False)
    temporary.close()
    writer = cv2.VideoWriter(temporary.name, cv2.VideoWriter_fourcc(*"MJPG"), 10, (96, 96))
    if not writer.isOpened():
        os.remove(temporary.name)
        raise RuntimeError("OpenCV could not create a temporary AVI test video.")
    for frame_number in range(12):
        frame = np.full((96, 96, 3), (20, 80 + frame_number * 8, 180), dtype=np.uint8)
        cv2.circle(frame, (15 + frame_number * 5, 48), 12, (240, 240, 240), -1)
        writer.write(frame)
    writer.release()
    with open(temporary.name, "rb") as video_file:
        content = video_file.read()
    os.remove(temporary.name)
    return content


def run_video_smoke_test():
    verification_id = None
    client = TestClient(app)
    try:
        with client:
            response = client.post(
                "/api/video/analyze",
                files={"file": ("sample.avi", make_video(), "video/x-msvideo")},
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            verification_id = payload["verification_id"]
            assert payload["verification_type"] == "VIDEO"
            assert payload["forensics"]["sampled_frames"] > 0

            details = client.get(f"/api/history/{verification_id}")
            assert details.status_code == 200, details.text
            assert details.json()["verification_type"] == "VIDEO"
        print("[PASS] Video frame sampling, scoring, SQLite history, and details flow works.")
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
            upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "videos"))
            for filename in os.listdir(upload_dir):
                if filename.startswith(verification_id):
                    os.remove(os.path.join(upload_dir, filename))


if __name__ == "__main__":
    run_video_smoke_test()
