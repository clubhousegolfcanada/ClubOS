from fastapi import APIRouter
from datetime import datetime
import os
from database import SessionLocal

router = APIRouter()

@router.get("/health/deep")
async def deep_health_check():
    db_status = "unreachable"
    email_status = "missing"

    # Check database connection
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "ok"
    except:
        db_status = "fail"

    # Check email env
    if os.getenv("EMAIL_USER") and os.getenv("EMAIL_PASSWORD"):
        email_status = "ok"

    return {
        "status": "ok",
        "timestamp": datetime.now(),
        "checks": {
            "database": db_status,
            "email_env": email_status
        }
    }
