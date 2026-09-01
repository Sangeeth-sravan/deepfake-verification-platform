from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class VerificationRecordBase(BaseModel):
    verification_id: str = Field(..., description="Unique verification reference code")
    verification_type: str = Field(..., description="Type of scan: IMAGE, VIDEO, AUDIO, DIGITAL_IDENTITY")
    result: str = Field(..., description="Classification outcome: REAL, VERIFIED, FAKE, DEEPFAKE_SUSPECTED, MANIPULATED")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    risk_score: int = Field(..., ge=0, le=100, description="Computed risk score between 0 and 100")
    risk_level: str = Field(..., description="Risk tier: LOW, MEDIUM, HIGH")
    filename: Optional[str] = Field(None, description="Original uploaded filename")
    details: Optional[str] = Field(None, description="JSON formatted string of forensic signals & explanations")

class VerificationRecordCreate(VerificationRecordBase):
    pass

class VerificationRecordResponse(VerificationRecordBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HealthStatusResponse(BaseModel):
    status: str
    service: str
    database: str
