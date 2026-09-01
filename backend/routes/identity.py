"""Phase 8 – Identity Verification Route
POST /api/identity/verify

Accepts two image uploads:
  - id_document  : photo of the identity document (passport, national ID, licence)
  - selfie       : front-facing portrait of the subject

Runs IdentityForensicAnalyzer and persists the result as a DIGITAL_IDENTITY
VerificationRecord in the existing SQLite database.
"""

import json
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config import settings
from database.connection import get_db
from database.models import VerificationRecord
from services.identity_analysis import IdentityForensicAnalyzer

router = APIRouter(tags=["Identity Verification"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_IDENTITY_MB = 15


def _validate_image_upload(upload: UploadFile, label: str) -> None:
    """Raise HTTP 400 if the upload is missing, has a bad extension, or wrong MIME type."""
    if not upload or not upload.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No {label} file provided.",
        )
    ext = os.path.splitext(upload.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS or upload.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"{label} must be a JPEG, PNG, or WEBP image "
                f"(received '{upload.filename}', content-type '{upload.content_type}')."
            ),
        )


async def _save_upload(contents: bytes, subdir: str, prefix: str, ext: str) -> str:
    """Save raw bytes to uploads/<subdir>/<prefix>_<random><ext> and return the path."""
    upload_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", settings.UPLOAD_DIR, subdir)
    )
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{prefix}_{uuid.uuid4().hex[:6]}{ext}"
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as fh:
        fh.write(contents)
    return path


@router.post(
    "/identity/verify",
    summary="Digital Identity Verification",
    description=(
        "Upload an ID document image and a selfie portrait. "
        "Runs Error Level Analysis, face detection, passive liveness check, "
        "and ORB cross-image similarity scoring. "
        "Persists the verification record in the SQLite database."
    ),
)
async def verify_identity(
    id_document: UploadFile = File(..., description="Photo of ID document (passport / national ID / licence)"),
    selfie: UploadFile = File(..., description="Front-facing selfie portrait"),
    db: Session = Depends(get_db),
):
    # 1. Validate both uploads
    _validate_image_upload(id_document, "ID document")
    _validate_image_upload(selfie, "Selfie")

    max_bytes = MAX_IDENTITY_MB * 1024 * 1024

    id_contents = await id_document.read()
    if len(id_contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"ID document exceeds the {MAX_IDENTITY_MB} MB limit.",
        )

    selfie_contents = await selfie.read()
    if len(selfie_contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Selfie image exceeds the {MAX_IDENTITY_MB} MB limit.",
        )

    # 2. Generate unique verification ID and save files
    verification_id = f"IDV-{uuid.uuid4().hex[:6].upper()}"
    id_ext = os.path.splitext(id_document.filename)[1].lower()
    selfie_ext = os.path.splitext(selfie.filename)[1].lower()

    id_saved_path = await _save_upload(id_contents, "identity", f"{verification_id}_id", id_ext)
    selfie_saved_path = await _save_upload(selfie_contents, "identity", f"{verification_id}_selfie", selfie_ext)

    try:
        # 3. Run forensic analysis
        forensics = IdentityForensicAnalyzer.analyze(id_saved_path, selfie_saved_path)

        # 4. Derive classification
        prediction = IdentityForensicAnalyzer.predict(forensics)

        # 5. Build details payload
        details_payload = {
            "forensics": forensics,
            "detected_issues": prediction["suspicious_indicators"],
            "explanation": prediction["explanation"],
            "model_name": prediction["model_name"],
        }

        # 6. Persist to SQLite
        record = VerificationRecord(
            verification_id=verification_id,
            verification_type="DIGITAL_IDENTITY",
            result=prediction["classification"],
            confidence=prediction["confidence"],
            risk_score=prediction["risk_score"],
            risk_level=prediction["risk_level"],
            filename=id_document.filename,          # store original ID doc name
            details=json.dumps(details_payload),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # 7. Return response
        return {
            "verification_id": verification_id,
            "verification_type": "DIGITAL_IDENTITY",
            "result": prediction["classification"],
            "confidence": prediction["confidence"],
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "filename": id_document.filename,
            "detected_issues": prediction["suspicious_indicators"],
            "explanation": prediction["explanation"],
            "forensics": forensics,
            "timestamp": record.created_at.isoformat(),
        }

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Identity verification processing failed: {exc}",
        )
