from dotenv import load_dotenv
from bootstrap import validate_env
load_dotenv()
validate_env()

# Then change the engine import:
# from engine import OperationalEngine
from engine_foundation import OperationalEngine
from fastapi import FastAPI, HTTPException
from health import router as health_router
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from schemas import TaskRequest, FormData, TaskResult
from datetime import datetime
import openai
import os

from database import SessionLocal, Equipment, Procedure, IncidentLog
from engine import OperationalEngine

app = FastAPI(title="ClubOS", version="2.0")

app.include_router(health_router)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
openai.api_key = os.getenv("OPENAI_API_KEY")
engine = OperationalEngine()

@app.post("/process")
async def process_task(request: TaskRequest):
    """Process operational request"""
    try:
        result = await engine.process_request(request.dict())
        
        # Log to database
        db = SessionLocal()
        log = IncidentLog(
            issue_description=request.task,
            location=request.location,
            timestamp=datetime.now()
        )
        db.add(log)
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "request_id": str(log.id),
            "response": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "2.0"
    }

@app.get("/equipment/{location}")
async def get_equipment(location: str):
    """Get equipment for a location"""
    db = SessionLocal()
    equipment = db.query(Equipment).filter(Equipment.location == location).all()
    db.close()
    
    return {
        "location": location,
        "equipment": [
            {
                "id": e.id,
                "type": e.equipment_type,
                "bay": e.bay_number,
                "model": e.model
            } for e in equipment
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)