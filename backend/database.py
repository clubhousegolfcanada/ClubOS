from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://clubos:password@localhost/clubos")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True)
    location = Column(String(100))
    bay_number = Column(Integer)
    equipment_type = Column(String(50))
    model = Column(String(100))
    serial_number = Column(String(100))
    common_issues = Column(JSON)
    troubleshooting_steps = Column(JSON)
    last_maintenance = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Procedure(Base):
    __tablename__ = "procedures"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    category = Column(String(50))
    steps = Column(JSON)
    estimated_time = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IncidentLog(Base):
    __tablename__ = "incident_log"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = Column(String(100))
    equipment_id = Column(Integer)
    issue_description = Column(Text)
    resolution = Column(Text)
    time_to_resolve = Column(Integer)
    resolved_by = Column(String(100))
    
# Create all tables
Base.metadata.create_all(bind=engine)