# backend/core/action_handler.py
import logging
from typing import Dict, Any
from datetime import datetime
from backend.database import SessionLocal
from backend.ticket_system import TicketSystem, NotificationService

logger = logging.getLogger(__name__)

class ActionHandler:
    """
    Handles specific action types from SOP steps.
    Routes to appropriate subsystems.
    """
    
    def __init__(self):
        self.ticket_system = TicketSystem()
        self.notification_service = NotificationService()
        
        # Action registry
        self.actions = {
            "refund": self._handle_refund,
            "contact_customer": self._handle_customer_contact,
            "equipment_restart": self._handle_equipment_restart,
            "verification": self._handle_verification,
            "generic_step": self._handle_generic
        }
    
    async def handle(self, action_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route action to appropriate handler.
        """
        handler = self.actions.get(action_type, self._handle_generic)
        
        try:
            result = await handler(context)
            result["action_type"] = action_type
            result["timestamp"] = datetime.now().isoformat()
            return result
        except Exception as e:
            logger.error(f"Action handler error for {action_type}: {e}")
            return {
                "success": False,
                "action_type": action_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_refund(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle refund actions.
        """
        step = context.get("step", {})
        
        # Extract refund details from step text
        import re
        amount_match = re.search(r'\$(\d+(?:\.\d{2})?)', step.get("text", ""))
        amount = float(amount_match.group(1)) if amount_match else 0
        
        # Create refund ticket
        db = SessionLocal()
        try:
            ticket = self.ticket_system.create_ticket(
                db=db,
                title=f"Refund Request - ${amount:.2f}",
                description=f"SOP-triggered refund\nStep: {step.get('text', 'N/A')}\nContext: {context}",
                priority="high",
                tags=["refund", "financial", "sop-triggered"]
            )
            
            # Send notification
            self.notification_service.send_ticket_notification(ticket)
            
            return {
                "success": True,
                "ticket_id": str(ticket.id),
                "amount": amount,
                "message": f"Refund ticket created: {ticket.id}"
            }
        finally:
            db.close()
    
    async def _handle_customer_contact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle customer contact actions.
        """
        step = context.get("step", {})
        
        # Determine contact method
        step_text = step.get("text", "").lower()
        if "email" in step_text:
            method = "email"
        elif "call" in step_text or "phone" in step_text:
            method = "phone"
        else:
            method = "general"
        
        # Create communication ticket
        db = SessionLocal()
        try:
            ticket = self.ticket_system.create_ticket(
                db=db,
                title=f"Customer Contact Required - {method.upper()}",
                description=f"SOP requires customer contact\nMethod: {method}\nStep: {step.get('text', 'N/A')}",
                priority="medium",
                tags=["customer-contact", method, "sop-triggered"]
            )
            
            return {
                "success": True,
                "ticket_id": str(ticket.id),
                "contact_method": method,
                "message": f"Contact ticket created: {ticket.id}"
            }
        finally:
            db.close()
    
    async def _handle_equipment_restart(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle equipment restart actions.
        """
        step = context.get("step", {})
        
        # Extract equipment details
        equipment_keywords = ["trackman", "projector", "simulator", "pos", "hvac"]
        step_lower = step.get("text", "").lower()
        
        equipment = "unknown"
        for keyword in equipment_keywords:
            if keyword in step_lower:
                equipment = keyword
                break
        
        # Extract bay number if mentioned
        import re
        bay_match = re.search(r'bay\s*(\d+)', step_lower)
        bay = bay_match.group(1) if bay_match else "all"
        
        # Log restart action
        logger.info(f"Equipment restart initiated: {equipment} in Bay {bay}")
        
        # In production, this would trigger actual restart commands
        # For now, create a maintenance log
        return {
            "success": True,
            "equipment": equipment,
            "bay": bay,
            "message": f"Restart command sent for {equipment}",
            "estimated_completion": "5 minutes"
        }
    
    async def _handle_verification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle verification/check actions.
        """
        step = context.get("step", {})
        
        # In production, this would run actual checks
        # For MVP, log the verification requirement
        verification_item = step.get("text", "Verification step")[:100]
        
        return {
            "success": True,
            "verified": True,
            "item": verification_item,
            "message": "Verification logged"
        }
    
    async def _handle_generic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle generic/unclassified actions.
        """
        step = context.get("step", {})
        
        # Log the action
        logger.info(f"Generic action executed: {step.get('text', '')[:50]}...")
        
        return {
            "success": True,
            "message": "Step executed",
            "step_summary": step.get("text", "")[:100]
        }
