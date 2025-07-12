# backend/routes/process.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import uuid
from datetime import datetime

from backend.schemas import ProcessRequest, ProcessResponse, ClubCoreLLMResponse
from backend.core.prompt import PromptBuilder
from backend.core.llm import llm_service
from backend.core.validator import ResponseValidator
from backend.core.fallback import FallbackService
from backend.database import get_db, SessionLocal
from backend.ticket_system import TicketSystem, NotificationService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
ticket_system = TicketSystem()
notification_service = NotificationService()

@router.post("/process", response_model=ProcessResponse)
async def process_task(request: ProcessRequest) -> ProcessResponse:
    """
    Process a task using LLM with fallback to rule-based logic.
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Processing request {request_id}: {request.task}")
    
    try:
        # Build context with location if provided
        context = request.context.copy()
        if request.location:
            context["location"] = request.location
        
        # Extract pricing information if mentioned
        import re
        price_match = re.search(r'\$(\d+)', request.task)
        if price_match:
            context["current_price"] = int(price_match.group(1))
        
        # Check if LLM is enabled
        if request.toggles.get("use_llm", True):
            try:
                logger.info(f"Attempting LLM processing for request {request_id}")
                
                # Build prompts
                system_prompt = PromptBuilder.build_system_prompt()
                task_prompt = PromptBuilder.build_task_prompt(
                    task=request.task,
                    priority=request.priority,
                    operation=request.operation,
                    toggles=request.toggles,
                    context=context
                )
                
                # Get LLM response
                llm_response = await llm_service.get_completion(task_prompt, system_prompt)
                
                # Validate LLM response
                validated_response = ResponseValidator.validate_llm_response(llm_response)
                
                if validated_response:
                    logger.info(f"Successfully processed task {request_id} via LLM")
                    response = validated_response
                else:
                    logger.warning(f"LLM validation failed for request {request_id}, using fallback")
                    response = FallbackService.process_with_rules({
                        "task": request.task,
                        "priority": request.priority,
                        "operation": request.operation,
                        "toggles": request.toggles,
                        "context": context,
                        "location": request.location
                    })
            except Exception as e:
                logger.error(f"LLM processing error for request {request_id}: {e}")
                response = FallbackService.process_with_rules({
                    "task": request.task,
                    "priority": request.priority,
                    "operation": request.operation,
                    "toggles": request.toggles,
                    "context": context,
                    "location": request.location
                })
        else:
            # LLM disabled, use fallback directly
            logger.info(f"LLM disabled for request {request_id}, using rule-based logic")
            response = FallbackService.process_with_rules({
                "task": request.task,
                "priority": request.priority,
                "operation": request.operation,
                "toggles": request.toggles,
                "context": context,
                "location": request.location
            })
        
        # Handle ticket generation if requested and ticket exists in response
        if request.toggles.get("generate_ticket", True) and response.ticket:
            try:
                db = SessionLocal()
                ticket = ticket_system.create_ticket(
                    db=db,
                    title=response.ticket.title,
                    description=response.ticket.description,
                    priority=response.ticket.priority,
                    tags=response.ticket.tags
                )
                
                # Send notification if enabled
                if request.toggles.get("send_notification", False):
                    notification_sent = notification_service.send_ticket_notification(ticket)
                    if notification_sent:
                        logger.info(f"Notification sent for ticket {ticket.id}")
                    else:
                        logger.warning(f"Failed to send notification for ticket {ticket.id}")
                
                # Add ticket ID to response
                response.ticket.id = str(ticket.id)
                
                db.close()
                logger.info(f"Ticket created: {ticket.id}")
            except Exception as e:
                logger.error(f"Failed to create ticket: {e}")
        
        # Log to console (this would be picked up by the UI)
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": f"Processed: {request.task[:50]}... | Status: {response.status} | Confidence: {response.confidence:.1%}",
            "type": "success" if response.status == "approved" else "warning"
        }
        logger.info(log_entry)
        
        return ProcessResponse(
            request_id=request_id,
            response=response
        )
        
    except Exception as e:
        logger.error(f"Fatal error processing request {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
