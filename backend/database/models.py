from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from database.connection import Base

class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    verification_id = Column(String(64), unique=True, index=True, nullable=False)
    verification_type = Column(String(32), nullable=False)  # IMAGE, VIDEO, AUDIO, DIGITAL_IDENTITY
    result = Column(String(32), nullable=False)             # REAL, VERIFIED, FAKE, DEEPFAKE_SUSPECTED, MANIPULATED
    confidence = Column(Float, nullable=False)              # 0.0 to 1.0
    risk_score = Column(Integer, nullable=False)            # 0 to 100
    risk_level = Column(String(16), nullable=False)         # LOW, MEDIUM, HIGH
    filename = Column(String(255), nullable=True)           # Uploaded file basename (no raw sensitive docs)
    details = Column(Text, nullable=True)                   # JSON string of forensic signals, issues, & explanation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<VerificationRecord(verification_id='{self.verification_id}', type='{self.verification_type}', result='{self.result}')>"
