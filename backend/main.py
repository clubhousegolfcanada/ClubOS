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
# Add these endpoints to your main.py after the existing ones

from ticket_system import TicketEngine

# Initialize ticket engine
ticket_engine = TicketEngine()

@app.post("/tickets")
async def create_ticket(ticket_request: dict):
    """Create a new ticket"""
    try:
        ticket = ticket_engine.create_ticket(
            ticket_request.get('task_result', {}), 
            ticket_request.get('form_data', {})
        )
        
        return {
            "status": "success",
            "ticket": {
                "id": ticket["id"],
                "assigned_to": ticket["assigned_to"],
                "category": ticket["category"],
                "priority": ticket["priority"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")

@app.get("/tickets")
async def get_tickets():
    """Get all tickets"""
    try:
        tickets = ticket_engine.get_all_tickets()
        return {"tickets": tickets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tickets: {str(e)}")

@app.post("/tickets/{ticket_id}/toggle")
async def toggle_ticket_status(ticket_id: str):
    """Toggle ticket status between active and inactive"""
    try:
        success = ticket_engine.toggle_ticket_status(ticket_id)
        
        if success:
            return {"status": "success", "message": f"Ticket {ticket_id} status toggled"}
        else:
            raise HTTPException(status_code=404, detail="Ticket not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle ticket: {str(e)}")

@app.get("/system/status")
async def system_status():
    """Get comprehensive system status"""
    db = SessionLocal()
    try:
        # Count various entities
        equipment_count = db.query(Equipment).count()
        active_incidents = db.query(IncidentLog).filter(IncidentLog.status == 'open').count()
        active_tickets = len([t for t in ticket_engine.get_all_tickets() if t['status'] == 'active'])
        
        # Get equipment status breakdown
        equipment_status = {}
        equipment_list = db.query(Equipment).all()
        for eq in equipment_list:
            status = eq.status
            equipment_status[status] = equipment_status.get(status, 0) + 1
        
        return {
            "status": "operational",
            "timestamp": datetime.now(),
            "metrics": {
                "total_equipment": equipment_count,
                "active_incidents": active_incidents,
                "active_tickets": active_tickets,
                "equipment_status": equipment_status
            },
            "layers": {
                "capability_frontier": "active",
                "clubops": "active", 
                "signalos": "active",
                "clubhost": "active",
                "ticket_engine": "active" if TicketEngine else "disabled"
            }
        }
    finally:
        db.close()

@app.get("/equipment")
async def list_all_equipment():
    """Get all equipment with status"""
    db = SessionLocal()
    try:
        equipment = db.query(Equipment).all()
        
        return {
            "equipment": [
                {
                    "id": e.id,
                    "location": e.location,
                    "bay": e.bay_number,
                    "type": e.equipment_type,
                    "model": e.model,
                    "status": e.status,
                    "last_maintenance": e.last_maintenance.isoformat() if e.last_maintenance else None,
                    "usage_hours": e.usage_hours or 0
                } for e in equipment
            ],
            "count": len(equipment)
        }
    finally:
        db.close()

@app.post("/equipment/{equipment_id}/status")
async def update_equipment_status(equipment_id: int, status_data: dict):
    """Update equipment status"""
    db = SessionLocal()
    try:
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        equipment.status = status_data.get('status', equipment.status)
        if 'usage_hours' in status_data:
            equipment.usage_hours = status_data['usage_hours']
        
        equipment.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "equipment_id": equipment_id,
            "new_status": equipment.status
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/analytics/summary")
async def analytics_summary():
    """Get analytics summary for dashboard"""
    db = SessionLocal()
    try:
        # Get counts
        total_incidents = db.query(IncidentLog).count()
        open_incidents = db.query(IncidentLog).filter(IncidentLog.status == 'open').count()
        resolved_incidents = db.query(IncidentLog).filter(IncidentLog.status == 'resolved').count()
        
        # Get recent activity
        recent_incidents = db.query(IncidentLog).order_by(
            IncidentLog.timestamp.desc()
        ).limit(10).all()
        
        return {
            "summary": {
                "total_incidents": total_incidents,
                "open_incidents": open_incidents,
                "resolved_incidents": resolved_incidents,
                "resolution_rate": round(resolved_incidents / max(total_incidents, 1) * 100, 1)
            },
            "recent_activity": [
                {
                    "id": i.id,
                    "description": i.issue_description[:100] + "..." if len(i.issue_description) > 100 else i.issue_description,
                    "category": i.issue_category,
                    "priority": i.priority,
                    "status": i.status,
                    "timestamp": i.timestamp.isoformat()
                } for i in recent_incidents
            ]
        }
    finally:
        db.close()
# Add these imports to your existing main.py
from backend.routes.process import router as process_router

# In your existing main.py, update the route registration section:
# (Add this where you register other routers)
app.include_router(process_router, prefix="/api", tags=["process"])

# Also ensure you have these middleware configurations:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
