"""
ClubOS Database Models and Configuration
SQLAlchemy ORM models for all ClubOS data
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://clubos:password@localhost/clubos")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Validate connections before use
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Equipment(Base):
    """Equipment tracking model"""
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True)
    location = Column(String(100), nullable=False)
    bay_number = Column(Integer)
    equipment_type = Column(String(50), nullable=False)  # trackman, projector, simulator
    model = Column(String(100))
    serial_number = Column(String(100))
    status = Column(String(20), default='online')  # online, offline, maintenance, error
    common_issues = Column(JSON)
    troubleshooting_steps = Column(JSON)
    last_maintenance = Column(DateTime)
    usage_hours = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Procedure(Base):
    """Standard Operating Procedures model"""
    __tablename__ = "procedures"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50))  # opening, closing, emergency, maintenance
    description = Column(Text)
    steps = Column(JSON)  # Array of step descriptions
    estimated_time = Column(Integer)  # Minutes
    required_roles = Column(JSON)  # Array of roles that can perform
    version = Column(String(10), default='1.0')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IncidentLog(Base):
    """Incident and issue tracking"""
    __tablename__ = "incident_log"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = Column(String(100))
    equipment_id = Column(Integer)  # References Equipment.id
    issue_description = Column(Text, nullable=False)
    issue_category = Column(String(50))  # equipment, facilities, general, emergency
    priority = Column(String(20))  # low, medium, high, critical
    status = Column(String(20), default='open')  # open, in_progress, resolved, closed
    resolution = Column(Text)
    time_to_resolve = Column(Integer)  # Minutes
    resolved_by = Column(String(100))
    confidence_score = Column(Float)  # AI processing confidence
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

class Ticket(Base):
    """Ticket management system"""
    __tablename__ = "tickets"
    
    id = Column(String(20), primary_key=True)  # TKT-123456
    task_id = Column(String(50))
    incident_id = Column(Integer)  # References IncidentLog.id
    category = Column(String(50), nullable=False)  # facilities, equipment, general, emergency
    priority = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(200))
    description = Column(Text, nullable=False)
    assigned_to = Column(String(100), nullable=False)
    contact_info = Column(JSON)  # {"name": "Nick", "phone": "281-XXX-XXXX", "email": "nick@example.com"}
    next_steps = Column(JSON)  # Array of recommended steps
    status = Column(String(20), default='active')  # active, inactive, completed
    notify_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

class TaskHistory(Base):
    """AI task processing history"""
    __tablename__ = "task_history"
    
    id = Column(Integer, primary_key=True)
    request_id = Column(String(50))
    task_description = Column(Text, nullable=False)
    task_category = Column(String(50))
    priority = Column(String(20))
    location = Column(String(100))
    
    # Processing results
    processing_time = Column(Float)  # Seconds
    confidence_score = Column(Float)
    recommendations = Column(JSON)  # Array of recommendations
    layers_processed = Column(JSON)  # Which layers processed this task
    
    # Engine details
    engine_version = Column(String(20), default='2.0')
    model_used = Column(String(50))  # OpenAI model if used
    
    # Outcomes
    ticket_generated = Column(Boolean, default=False)
    ticket_id = Column(String(20))  # References Ticket.id
    status = Column(String(20), default='completed')  # completed, failed, processing
    
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemLog(Base):
    """System events and monitoring"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20), nullable=False)  # info, warning, error, critical
    component = Column(String(50))  # engine, database, email, etc.
    event_type = Column(String(50))  # startup, shutdown, error, processing
    message = Column(Text, nullable=False)
    details = Column(JSON)  # Additional structured data
    user_id = Column(String(50))  # If user-related
    session_id = Column(String(50))  # Request session

def init_database():
    """Initialize database tables and default data"""
    print("🗄️  Initializing ClubOS database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Add default equipment data
    db = SessionLocal()
    try:
        # Check if we already have equipment data
        existing_equipment = db.query(Equipment).first()
        if not existing_equipment:
            print("📦 Adding default equipment data...")
            
            # Default equipment for bays 1-8
            default_equipment = [
                {"location": "River Oaks", "bay_number": 1, "equipment_type": "trackman", "model": "TrackMan 4", "status": "online"},
                {"location": "River Oaks", "bay_number": 1, "equipment_type": "projector", "model": "Epson Pro L1755U", "status": "online"},
                {"location": "River Oaks", "bay_number": 2, "equipment_type": "trackman", "model": "TrackMan 4", "status": "online"},
                {"location": "River Oaks", "bay_number": 2, "equipment_type": "projector", "model": "Epson Pro L1755U", "status": "online"},
                {"location": "River Oaks", "bay_number": 3, "equipment_type": "trackman", "model": "TrackMan 4", "status": "maintenance"},
                {"location": "River Oaks", "bay_number": 3, "equipment_type": "projector", "model": "Epson Pro L1755U", "status": "online"},
                {"location": "River Oaks", "bay_number": 4, "equipment_type": "trackman", "model": "TrackMan 4", "status": "online"},
                {"location": "River Oaks", "bay_number": 4, "equipment_type": "projector", "model": "Epson Pro L1755U", "status": "online"},
            ]
            
            for eq_data in default_equipment:
                equipment = Equipment(**eq_data)
                db.add(equipment)
            
            db.commit()
            print(f"✅ Added {len(default_equipment)} equipment records")
        
        # Add default procedures
        existing_procedures = db.query(Procedure).first()
        if not existing_procedures:
            print("📋 Adding default procedures...")
            
            opening_procedure = Procedure(
                name="Daily Opening Procedure",
                category="opening",
                description="Standard opening checklist for daily operations",
                steps=[
                    "Disarm alarm system",
                    "Turn on main power switches behind bar", 
                    "Boot up all simulator systems",
                    "Check each bay for leftover items",
                    "Test TrackMan units (hit one shot each bay)",
                    "Turn on music system",
                    "Unlock front entrance",
                    "Flip OPEN sign"
                ],
                estimated_time=30
            )
            
            closing_procedure = Procedure(
                name="Daily Closing Procedure", 
                category="closing",
                description="Standard closing checklist",
                steps=[
                    "Announce closing 30 minutes prior",
                    "Stop accepting new customers 1 hour before close",
                    "Shut down simulators in sequence (Bays 1-8)",
                    "Clean all hitting areas and retrieve balls",
                    "Lock alcohol storage cabinet",
                    "Set alarm to AWAY mode",
                    "Text manager confirmation of closure"
                ],
                estimated_time=45
            )
            
            db.add(opening_procedure)
            db.add(closing_procedure)
            db.commit()
            print("✅ Added default procedures")
        
        print("🎯 Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        db.rollback()
    finally:
        db.close()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database on import
if __name__ == "__main__":
    init_database()
