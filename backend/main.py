from dotenv import load_dotenv
from bootstrap import validate_env

# Load environment first
load_dotenv()
validate_env()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from health import router as health_router
from schemas import TaskRequest, FormData, TaskResult
from datetime import datetime
import openai
import os
import traceback

# Import our unified engine
from engine_foundation import OperationalEngine
from database import SessionLocal, Equipment, Procedure, IncidentLog

# Initialize FastAPI app
app = FastAPI(
    title="ClubOS Mission Control",
    version="2.0",
    description="Central nervous system for Clubhouse 24/7 Golf operations"
)

# Add health router
app.include_router(health_router)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Initialize OpenAI and Engine
openai.api_key = os.getenv("OPENAI_API_KEY")
engine = OperationalEngine()

# Root endpoint - serve frontend
@app.get("/")
async def root():
    """Serve the main frontend application"""
    return FileResponse('../frontend/index.html')

@app.post("/process")
async def process_task(request: TaskRequest):
    """Process operational request through the engine layers"""
    try:
        # Process through the cognitive engine
        result = await engine.process_request(request.dict())
        
        # Log to database
        db = SessionLocal()
        try:
            log = IncidentLog(
                issue_description=request.task,
                location=request.location,
                timestamp=datetime.now()
            )
            db.add(log)
            db.commit()
            request_id = str(log.id)
        except Exception as db_error:
            print(f"Database logging failed: {db_error}")
            request_id = f"req_{int(datetime.now().timestamp())}"
        finally:
            db.close()
        
        return {
            "status": "success",
            "request_id": request_id,
            "response": result
        }
        
    except Exception as e:
        print(f"Processing error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "type": "processing_error",
                "message": "Failed to process request through engine layers"
            }
        )

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "2.0",
        "engine": "operational",
        "layers": ["CapabilityFrontier", "ClubOps", "SignalOS", "Clubhost", "TicketEngine"]
    }

@app.get("/equipment/{location}")
async def get_equipment(location: str):
    """Get equipment for a specific location"""
    db = SessionLocal()
    try:
        equipment = db.query(Equipment).filter(
            Equipment.location.ilike(f"%{location}%")
        ).all()
        
        return {
            "location": location,
            "equipment": [
                {
                    "id": e.id,
                    "type": e.equipment_type,
                    "bay": e.bay_number,
                    "model": e.model,
                    "serial": e.serial_number,
                    "last_maintenance": e.last_maintenance.isoformat() if e.last_maintenance else None
                } for e in equipment
            ],
            "count": len(equipment)
        }
    finally:
        db.close()

@app.get("/incidents")
async def get_incidents(limit: int = 50):
    """Get recent incident logs"""
    db = SessionLocal()
    try:
        incidents = db.query(IncidentLog).order_by(
            IncidentLog.timestamp.desc()
        ).limit(limit).all()
        
        return {
            "incidents": [
                {
                    "id": i.id,
                    "timestamp": i.timestamp.isoformat(),
                    "location": i.location,
                    "description": i.issue_description,
                    "resolution": i.resolution,
                    "resolved_by": i.resolved_by,
                    "time_to_resolve": i.time_to_resolve
                } for i in incidents
            ],
            "count": len(incidents)
        }
    finally:
        db.close()

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error reporting"""
    print(f"Global exception: {exc}")
    print(traceback.format_exc())
    
    return {
        "status": "error",
        "message": str(exc),
        "type": type(exc).__name__,
        "path": str(request.url)
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting ClubOS Mission Control...")
    print("=" * 50)
    print("🧠 Engine: OperationalEngine with cognitive layers")
    print("🗄️  Database: PostgreSQL with SQLAlchemy ORM")
    print("🌐 Frontend: Custom HTML/CSS/JS interface")
    print("📧 Notifications: Email-based ticket system")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
