import json
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config import settings
from database.connection import get_db
from database.models import VerificationRecord
from services.audio_analysis import AudioForensicAnalyzer

router = APIRouter(tags=["Audio Verification"])
MAX_AUDIO_SIZE_MB = 20


@router.post("/audio/analyze", summary="Analyze WAV audio authenticity")
async def analyze_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No audio file provided.")
    extension = os.path.splitext(file.filename)[1].lower()
    if extension != ".wav" or file.content_type not in {"audio/wav", "audio/x-wav", "audio/wave"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This MVP supports uncompressed PCM WAV audio files only.")

    contents = await file.read()
    if len(contents) > MAX_AUDIO_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Audio file size exceeds {MAX_AUDIO_SIZE_MB}MB.")

    verification_id = f"AUD-{uuid.uuid4().hex[:6].upper()}"
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", settings.UPLOAD_DIR, "audio"))
    os.makedirs(upload_dir, exist_ok=True)
    saved_path = os.path.join(upload_dir, f"{verification_id}_{uuid.uuid4().hex[:4]}.wav")
    with open(saved_path, "wb") as output:
        output.write(contents)

    try:
        forensics = AudioForensicAnalyzer.analyze(saved_path)
        prediction = AudioForensicAnalyzer.predict(forensics)
        details = {"forensics": forensics, "detected_issues": prediction["suspicious_indicators"], "explanation": prediction["explanation"], "model_name": "Waveform & Spectral Forensic Analyzer v1.0"}
        record = VerificationRecord(verification_id=verification_id, verification_type="AUDIO", result=prediction["classification"], confidence=prediction["confidence"], risk_score=prediction["risk_score"], risk_level=prediction["risk_level"], filename=file.filename, details=json.dumps(details))
        db.add(record)
        db.commit()
        db.refresh(record)
        return {"verification_id": verification_id, "verification_type": "AUDIO", "result": prediction["classification"], "confidence": prediction["confidence"], "risk_score": prediction["risk_score"], "risk_level": prediction["risk_level"], "filename": file.filename, "detected_issues": prediction["suspicious_indicators"], "explanation": prediction["explanation"], "forensics": forensics, "timestamp": record.created_at.isoformat()}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Audio analysis failed: {error}")
