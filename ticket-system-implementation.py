# =====================================================
# 1. ENHANCED DATABASE MODEL (Add to database.py)
# =====================================================

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Add this new model to your existing database.py file

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(String(20), primary_key=True)  # TKT-123456
    task_id = Column(String(50))
    category = Column(String(50))  # facilities, equipment, general, emergency
    priority = Column(String(20))  # low, medium, high, critical
    description = Column(Text)
    assigned_to = Column(String(100))
    contact_info = Column(JSON)  # {"name": "Nick", "phone": "281-XXX-XXXX", "email": "nick@example.com"}
    next_steps = Column(JSON)  # Array of steps
    status = Column(String(20), default='active')  # active, inactive
    notify_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# =====================================================
# 2. TICKET SYSTEM (Create new file: ticket_system.py)
# =====================================================

import time
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from database import SessionLocal, Ticket
import os
from typing import Dict, List

# Contact assignment rules
CONTACT_ASSIGNMENT = {
    'facilities': {
        'name': 'Nick',
        'phone': '281-555-0101',
        'email': 'nick@clubhouse.com'
    },
    'equipment': {
        'name': 'Jason',
        'phone': '281-555-0102', 
        'email': 'jason@clubhouse.com'
    },
    'general': {
        'name': 'Manager',
        'phone': '281-555-0103',
        'email': 'manager@clubhouse.com'
    },
    'emergency': {
        'name': 'Mike',
        'phone': '281-555-0104',
        'email': 'mike@clubhouse.com'
    }
}

class NotificationService:
    """Simple email notification service using SMTP"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'clubos@yourclubhouse.com')
    
    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        """Send email notification"""
        if not self.email_user or not self.email_password:
            print("Email credentials not configured - notification skipped")
            return False
            
        try:
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Create HTML content
            html_part = MimeText(content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_ticket_notification(self, contact: Dict, ticket: 'TicketData') -> bool:
        """Send ticket notification email"""
        subject = f"🎯 ClubOS Ticket: {ticket.id} - {ticket.priority.upper()} Priority"
        
        # Priority color coding
        priority_colors = {
            'low': '#10b981',
            'medium': '#f59e0b', 
            'high': '#ef4444',
            'critical': '#dc2626'
        }
        color = priority_colors.get(ticket.priority, '#888')
        
        content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a1a; color: white; padding: 20px; border-radius: 8px;">
                <h2 style="color: #152F2F; margin: 0 0 20px 0;">🎯 New ClubOS Ticket Assignment</h2>
                
                <div style="background: #2a2a2a; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 12px 0;">Ticket Details</h3>
                    <p><strong>Ticket ID:</strong> {ticket.id}</p>
                    <p><strong>Priority:</strong> <span style="color: {color}; font-weight: bold;">{ticket.priority.upper()}</span></p>
                    <p><strong>Category:</strong> {ticket.category.title()}</p>
                    <p><strong>Assigned to:</strong> {contact['name']}</p>
                </div>
                
                <div style="background: #2a2a2a; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 12px 0;">Issue Description</h3>
                    <p style="line-height: 1.6;">{ticket.description}</p>
                </div>
                
                <div style="background: #2a2a2a; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 12px 0;">Recommended Next Steps</h3>
                    <ol style="line-height: 1.8; padding-left: 20px;">
        """
        
        for step in ticket.next_steps:
            content += f"<li>{step}</li>"
            
        content += f"""
                    </ol>
                </div>
                
                <div style="background: #152F2F; padding: 16px; border-radius: 6px; text-align: center;">
                    <p style="margin: 0; font-size: 14px;">
                        Please address this issue and update the ticket status in ClubOS when completed.
                    </p>
                </div>
                
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #3a3a3a; font-size: 12px; color: #888;">
                    <p>Generated by ClubOS Mission Control • {ticket.created_at}</p>
                </div>
            </div>
        </div>
        """
        
        return self.send_email(contact['email'], subject, content)

class TicketData:
    """Simple data class for ticket information"""
    def __init__(self, id, category, priority, description, assigned_to, contact_info, next_steps, status='active'):
        self.id = id
        self.category = category
        self.priority = priority
        self.description = description
        self.assigned_to = assigned_to
        self.contact_info = contact_info
        self.next_steps = next_steps
        self.status = status
        self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

class TicketEngine:
    """Simple ticket creation and management"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def create_ticket(self, task_result: Dict, form_data: Dict) -> TicketData:
        """Create a new ticket with contact assignment"""
        
        # Get category and assign contact
        category = form_data.get('category', 'general')
        contact = CONTACT_ASSIGNMENT.get(category, CONTACT_ASSIGNMENT['general'])
        
        # Generate ticket ID
        ticket_id = f"TKT-{int(time.time())}"
        
        # Create ticket data
        ticket_data = TicketData(
            id=ticket_id,
            category=category,
            priority=form_data.get('priority', 'medium'),
            description=task_result.get('task', 'No description provided'),
            assigned_to=contact['name'],
            contact_info=contact,
            next_steps=task_result.get('recommendation', ['Contact manager for assistance']),
            status='active'
        )
        
        # Save to database
        db = SessionLocal()
        try:
            ticket = Ticket(
                id=ticket_data.id,
                task_id=form_data.get('task_id', ''),
                category=ticket_data.category,
                priority=ticket_data.priority,
                description=ticket_data.description,
                assigned_to=ticket_data.assigned_to,
                contact_info=ticket_data.contact_info,
                next_steps=ticket_data.next_steps,
                status=ticket_data.status,
                notify_sent=False
            )
            
            db.add(ticket)
            db.commit()
            
            # Send notification if enabled
            if form_data.get('notify_enabled', False):
                notification_sent = self.notification_service.send_ticket_notification(
                    contact, ticket_data
                )
                
                if notification_sent:
                    ticket.notify_sent = True
                    db.commit()
                    print(f"Notification sent for ticket {ticket_id}")
                else:
                    print(f"Failed to send notification for ticket {ticket_id}")
            
            db.close()
            return ticket_data
            
        except Exception as e:
            db.rollback()
            db.close()
            print(f"Error creating ticket: {e}")
            raise e
    
    def get_all_tickets(self) -> List[Dict]:
        """Get all tickets from database"""
        db = SessionLocal()
        try:
            tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
            
            ticket_list = []
            for t in tickets:
                ticket_list.append({
                    "id": t.id,
                    "category": t.category,
                    "priority": t.priority,
                    "description": t.description,
                    "assigned_to": t.assigned_to,
                    "status": t.status,
                    "notify_sent": t.notify_sent,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "next_steps": t.next_steps or []
                })
            
            return ticket_list
            
        finally:
            db.close()
    
    def toggle_ticket_status(self, ticket_id: str) -> bool:
        """Toggle ticket between active and inactive"""
        db = SessionLocal()
        try:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                ticket.status = 'inactive' if ticket.status == 'active' else 'active'
                ticket.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"Error toggling ticket status: {e}")
            return False
        finally:
            db.close()

# =====================================================
# 3. UPDATE ENGINE (Modify engine_foundation.py)
# =====================================================

# Add this import at the top of engine_foundation.py
from ticket_system import TicketEngine

# Modify the TicketLogger class in engine_foundation.py
class TicketLogger:
    def __init__(self):
        self.db = SessionLocal()
        self.ticket_engine = TicketEngine()  # NEW

    def log(self, context, response):
        print(f"[LOGGED] Type={context['type']} | Equip={context['equipment']} | Loc={context['location']}")
        print(f"[RESOLUTION] {response.get('recommendation')}")
    
    def create_ticket_if_requested(self, task_result, form_data):
        """Create ticket if requested in form"""
        if form_data.get('generate_ticket', False):
            try:
                ticket = self.ticket_engine.create_ticket(task_result, form_data)
                return ticket
            except Exception as e:
                print(f"Failed to create ticket: {e}")
                return None
        return None

# =====================================================
# 4. UPDATE MAIN.PY API ENDPOINTS
# =====================================================

# Add these imports to main.py
from ticket_system import TicketEngine

# Add this new endpoint to main.py
@app.post("/tickets")
async def create_ticket(ticket_request: dict):
    """Create a new ticket"""
    try:
        ticket_engine = TicketEngine()
        ticket = ticket_engine.create_ticket(
            ticket_request.get('task_result', {}), 
            ticket_request.get('form_data', {})
        )
        
        return {
            "status": "success",
            "ticket": {
                "id": ticket.id,
                "assigned_to": ticket.assigned_to,
                "category": ticket.category,
                "priority": ticket.priority
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")

@app.get("/tickets")
async def get_tickets():
    """Get all tickets"""
    try:
        ticket_engine = TicketEngine()
        tickets = ticket_engine.get_all_tickets()
        return {"tickets": tickets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tickets: {str(e)}")

@app.post("/tickets/{ticket_id}/toggle")
async def toggle_ticket_status(ticket_id: str):
    """Toggle ticket status between active and inactive"""
    try:
        ticket_engine = TicketEngine()
        success = ticket_engine.toggle_ticket_status(ticket_id)
        
        if success:
            return {"status": "success", "message": f"Ticket {ticket_id} status toggled"}
        else:
            raise HTTPException(status_code=404, detail="Ticket not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle ticket: {str(e)}")

# =====================================================
# 5. ENVIRONMENT VARIABLES (Add to .env)
# =====================================================

# Add these to your .env file:
# EMAIL_USER=your-email@gmail.com
# EMAIL_PASSWORD=your-app-password
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# FROM_EMAIL=clubos@yourclubhouse.com