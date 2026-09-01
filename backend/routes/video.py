import json
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config import settings
from database.connection import get_db
from database.models import VerificationRecord
from models.deepfake.baseline_detector import BaselineForensicDetector
from services.video_analysis import VideoForensicAnalyzer

router = APIRouter(tags=["Video Verification"])

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".webm"}
ALLOWED_MIME_TYPES = {"video/mp4", "video/x-msvideo", "video/quicktime", "video/webm"}
detector_engine = BaselineForensicDetector()


@router.post("/video/analyze", summary="Analyze video authenticity")
async def analyze_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No video file provided.")
    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supported video formats: MP4, AVI, MOV, WEBM.")

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File size exceeds {settings.MAX_UPLOAD_SIZE_MB}MB.")

    verification_id = f"VID-{uuid.uuid4().hex[:6].upper()}"
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", settings.UPLOAD_DIR, "videos"))
    os.makedirs(upload_dir, exist_ok=True)
    saved_path = os.path.join(upload_dir, f"{verification_id}_{uuid.uuid4().hex[:4]}{extension}")
    with open(saved_path, "wb") as output:
        output.write(contents)

    try:
        forensics = VideoForensicAnalyzer.analyze(saved_path)
        prediction = detector_engine.predict(saved_path, forensics)
        issues = [f"Sampled {forensics['sampled_frames']} evenly distributed video frames.", *prediction["suspicious_indicators"]]
        details = {
            "forensics": forensics,
            "detected_issues": issues,
            "explanation": prediction["explanation"],
            "model_name": prediction["model_name"],
        }
        record = VerificationRecord(
            verification_id=verification_id,
            verification_type="VIDEO",
            result=prediction["classification"],
            confidence=prediction["confidence"],
            risk_score=prediction["risk_score"],
            risk_level=prediction["risk_level"],
            filename=file.filename,
            details=json.dumps(details),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "verification_id": verification_id,
            "verification_type": "VIDEO",
            "result": prediction["classification"],
            "confidence": prediction["confidence"],
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "filename": file.filename,
            "detected_issues": issues,
            "explanation": prediction["explanation"],
            "forensics": forensics,
            "timestamp": record.created_at.isoformat(),
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Video analysis failed: {error}")
