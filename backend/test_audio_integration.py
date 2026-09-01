"""Smoke test for the Phase 7 audio upload and persistence flow."""
import io
import math
import os
import sys
import wave

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


def make_wav() -> bytes:
    sample_rate = 16000
    duration_seconds = 1
    times = np.arange(sample_rate * duration_seconds) / sample_rate
    samples = (0.35 * np.sin(2 * math.pi * 440 * times) + 0.03 * np.sin(2 * math.pi * 1800 * times))
    pcm = np.clip(samples * 32767, -32768, 32767).astype("<i2")
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(pcm.tobytes())
    return output.getvalue()


def run_audio_smoke_test():
    verification_id = None
    client = TestClient(app)
    try:
        with client:
            response = client.post("/api/audio/analyze", files={"file": ("sample.wav", make_wav(), "audio/wav")})
            assert response.status_code == 200, response.text
            payload = response.json()
            verification_id = payload["verification_id"]
            assert payload["verification_type"] == "AUDIO"
            assert payload["forensics"]["sample_rate_hz"] == 16000

            details = client.get(f"/api/history/{verification_id}")
            assert details.status_code == 200, details.text
            assert details.json()["forensics"]["duration_seconds"] == 1.0

            report = client.get(f"/api/report/{verification_id}/download")
            assert report.status_code == 200, report.text
            assert report.content.startswith(b"%PDF-")
        print("[PASS] WAV analysis, SQLite history/details, and PDF report flow works.")
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
            upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "audio"))
            for filename in os.listdir(upload_dir):
                if filename.startswith(verification_id):
                    os.remove(os.path.join(upload_dir, filename))


if __name__ == "__main__":
    run_audio_smoke_test()
