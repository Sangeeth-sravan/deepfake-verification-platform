import os
import json
import uuid

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session

from config import settings
from database.connection import get_db
from database.models import VerificationRecord
from services.image_analysis import ImageForensicAnalyzer
from models.deepfake.baseline_detector import BaselineForensicDetector

router = APIRouter(tags=["Image Verification"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

detector_engine = BaselineForensicDetector()

@router.post(
    "/image/analyze",
    summary="Analyze Image Authenticity",
    description="Uploads an image file, runs Error Level Analysis (ELA), 2D Fourier Transform frequency inspection, and calculates forensic risk scores."
)
async def analyze_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Validate File Presence
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image file provided in upload request."
        )

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    # 2. Validate Extension & MIME Type
    if ext not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: JPG, PNG, WEBP."
        )

    # Read file content to check size and save
    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # 3. Save File Safely
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", settings.UPLOAD_DIR, "images"))
    os.makedirs(upload_dir, exist_ok=True)

    unique_code = f"IMG-{uuid.uuid4().hex[:6].upper()}"
    safe_filename = f"{unique_code}_{uuid.uuid4().hex[:4]}{ext}"
    saved_file_path = os.path.join(upload_dir, safe_filename)

    with open(saved_file_path, "wb") as f:
        f.write(contents)

    try:
        # 4. Perform Image Forensic Analysis
        forensic_data = ImageForensicAnalyzer.analyze(saved_file_path)

        # 5. Run Baseline Detector Prediction
        prediction = detector_engine.predict(saved_file_path, forensic_data)

        # Build full details payload
        details_payload = {
            "forensics": forensic_data,
            "detected_issues": prediction["suspicious_indicators"],
            "explanation": prediction["explanation"],
            "model_name": prediction["model_name"]
        }

        # 6. Save Record in SQLite Database
        db_record = VerificationRecord(
            verification_id=unique_code,
            verification_type="IMAGE",
            result=prediction["classification"],
            confidence=prediction["confidence"],
            risk_score=prediction["risk_score"],
            risk_level=prediction["risk_level"],
            filename=filename,
            details=json.dumps(details_payload)
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        # 7. Return Response JSON
        return {
            "verification_id": unique_code,
            "verification_type": "IMAGE",
            "result": prediction["classification"],
            "confidence": prediction["confidence"],
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "filename": filename,
            "detected_issues": prediction["suspicious_indicators"],
            "explanation": prediction["explanation"],
            "forensics": forensic_data,
            "timestamp": db_record.created_at.isoformat()
        }

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during forensic image processing: {str(e)}"
        )
