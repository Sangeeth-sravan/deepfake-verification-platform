from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database.connection import get_db
from schemas import HealthStatusResponse

router = APIRouter(tags=["Health"])

@router.get(
    "/health",
    response_model=HealthStatusResponse,
    summary="Platform API & Database Health Check",
    description="Returns operational status of the Deepfake Verification Platform API and its SQLite database."
)
async def check_health(db: Session = Depends(get_db)):
    db_status = "disconnected"
    try:
        # Execute lightweight ping query
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as err:
        db_status = f"error: {str(err)}"

    return {
        "status": "healthy",
        "service": "Deepfake Verification Platform API",
        "database": db_status
    }
