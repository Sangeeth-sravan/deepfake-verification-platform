import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import VerificationRecord

router = APIRouter(tags=["Verification History"])


def serialize_record(record: VerificationRecord, include_details: bool = False) -> dict:
    """Return a browser-friendly representation of a persisted verification."""
    payload = {
        "verification_id": record.verification_id,
        "verification_type": record.verification_type,
        "result": record.result,
        "confidence": record.confidence,
        "risk_score": record.risk_score,
        "risk_level": record.risk_level,
        "filename": record.filename,
        "timestamp": record.created_at.isoformat(),
    }
    if include_details:
        try:
            details = json.loads(record.details or "{}")
        except json.JSONDecodeError:
            details = {}
        payload.update({
            "forensics": details.get("forensics"),
            "detected_issues": details.get("detected_issues", []),
            "explanation": details.get("explanation"),
            "model_name": details.get("model_name"),
        })
    return payload


@router.get("/history", summary="List verification history")
async def get_history(
    limit: int = Query(default=100, ge=1, le=500),
    verification_type: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(VerificationRecord)
    if verification_type:
        query = query.filter(VerificationRecord.verification_type == verification_type.upper())
    if risk_level:
        query = query.filter(VerificationRecord.risk_level == risk_level.upper())
    records = query.order_by(VerificationRecord.created_at.desc()).limit(limit).all()
    return {"history": [serialize_record(record) for record in records], "count": len(records)}


@router.get("/history/{verification_id}", summary="Get one verification record")
async def get_verification_details(verification_id: str, db: Session = Depends(get_db)):
    record = db.query(VerificationRecord).filter(
        VerificationRecord.verification_id == verification_id.upper()
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification record not found.")
    return serialize_record(record, include_details=True)


@router.get("/stats", summary="Get verification statistics")
async def get_stats(db: Session = Depends(get_db)):
    type_counts = db.query(
        VerificationRecord.verification_type, func.count(VerificationRecord.verification_id)
    ).group_by(VerificationRecord.verification_type).all()
    
    risk_counts = db.query(
        VerificationRecord.risk_level, func.count(VerificationRecord.verification_id)
    ).group_by(VerificationRecord.risk_level).all()
    
    by_type = {"IMAGE": 0, "VIDEO": 0, "AUDIO": 0, "DIGITAL_IDENTITY": 0}
    by_type.update({item[0]: item[1] for item in type_counts})

    by_risk = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    by_risk.update({item[0]: item[1] for item in risk_counts})

    return {
        "by_type": by_type,
        "by_risk_level": by_risk,
    }
