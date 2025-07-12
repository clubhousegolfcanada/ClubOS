from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

class TaskRequest(BaseModel):
    task: str
    priority: Optional[str] = "normal"
    location: Optional[str] = None

class TaskResult(BaseModel):
    status: str
    confidence: float
    recommendation: List[str]
    time_estimate: Optional[str] = "Unknown"
    contact_if_fails: Optional[str] = "Manager"

class FormData(BaseModel):
    category: str
    priority: Optional[str] = "medium"
    task_id: Optional[str] = ""
    notify_enabled: Optional[bool] = False
    generate_ticket: Optional[bool] = False

class TicketData(BaseModel):
    id: str
    category: str
    priority: str
    description: str
    assigned_to: str
    contact_info: Dict[str, str]
    next_steps: List[str]
    status: str = "active"
    created_at: Optional[str] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
