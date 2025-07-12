# backend/core/fallback.py
from typing import Dict, Any
from backend.schemas import ClubCoreLLMResponse, Layer, Recommendation, Ticket
from backend.knowledge_base import KNOWLEDGE_BASE, CONTACT_ASSIGNMENT
import logging

logger = logging.getLogger(__name__)

class FallbackService:
    @staticmethod
    def process_with_rules(task_data: Dict[str, Any]) -> ClubCoreLLMResponse:
        logger.info("Using fallback rule-based logic")
        
        task = task_data.get("task", "").lower()
        priority = task_data.get("priority", "medium")
        context = task_data.get("context", {})
        location = task_data.get("location", "")
        
        # Price cap rule
        if "price" in task or "pricing" in task:
            current_price = context.get("current_price", 0)
            if current_price > 35:
                return ClubCoreLLMResponse(
                    layers=[
                        Layer(
                            name="pricing",
                            status="violation",
                            details=f"Price ${current_price}/hr exceeds $35/hr cap"
                        )
                    ],
                    recommendation=[
                        Recommendation(
                            action="Reduce pricing to $35/hr maximum",
                            reason="Corporate pricing cap exceeded",
                            priority="high"
                        )
                    ],
                    ticket=Ticket(
                        title="Pricing Cap Violation",
                        description=f"Bay pricing of ${current_price}/hr exceeds corporate maximum of $35/hr",
                        priority="high",
                        tags=["pricing", "compliance", "urgent"]
                    ),
                    status="review_required",
                    confidence=1.0,
                    time_estimate="Immediate",
                    fallback=True
                )
        
        # Equipment issues
        if any(equip in task for equip in ["trackman", "projector", "simulator", "bay"]):
            equipment_type = next((eq for eq in ["trackman", "projector", "simulator"] if eq in task), "equipment")
            bay_number = None
            
            # Extract bay number
            import re
            bay_match = re.search(r'bay\s*(\d+)', task)
            if bay_match:
                bay_number = bay_match.group(1)
            
            return ClubCoreLLMResponse(
                layers=[
                    Layer(
                        name="equipment",
                        status="malfunction",
                        details=f"{equipment_type.title()} issue detected"
                    ),
                    Layer(
                        name="facilities",
                        status="affected",
                        details=f"Bay {bay_number or 'unknown'} impacted"
                    )
                ],
                recommendation=[
                    Recommendation(
                        action="Initiate diagnostic protocol",
                        reason="Equipment malfunction reported",
                        priority="high"
                    ),
                    Recommendation(
                        action="Contact technical support",
                        reason="Specialized equipment requires expert attention",
                        priority="high"
                    )
                ],
                ticket=Ticket(
                    title=f"{equipment_type.title()} Malfunction - Bay {bay_number or 'Unknown'}",
                    description=f"Staff reported: {task_data.get('task', 'Equipment issue')}",
                    priority="high",
                    tags=["equipment", equipment_type, "technical", f"bay-{bay_number or 'unknown'}"]
                ),
                status="review_required",
                confidence=0.9,
                time_estimate="1-2 hours",
                fallback=True
            )
        
        # Installation requests
        if "install" in task:
            return ClubCoreLLMResponse(
                layers=[
                    Layer(name="operations", status="active"),
                    Layer(name="facilities", status="planning")
                ],
                recommendation=[
                    Recommendation(
                        action="Schedule installation window",
                        reason="Minimize operational disruption",
                        priority="medium"
                    ),
                    Recommendation(
                        action="Prepare installation checklist",
                        reason="Ensure all components ready",
                        priority="medium"
                    )
                ],
                ticket=Ticket(
                    title="Installation Request",
                    description=task_data.get("task", "New installation requested"),
                    priority=priority,
                    tags=["installation", "facilities", "planning"]
                ),
                status="approved",
                confidence=0.85,
                time_estimate="2-4 hours",
                fallback=True
            )
        
        # SOP requests
        if "sop" in task or "procedure" in task:
            return ClubCoreLLMResponse(
                layers=[
                    Layer(name="operations", status="active"),
                    Layer(name="compliance", status="referenced")
                ],
                recommendation=[
                    Recommendation(
                        action="Follow standard operating procedure",
                        reason="Established protocol exists",
                        priority="medium"
                    ),
                    Recommendation(
                        action="Document completion in log",
                        reason="Maintain compliance records",
                        priority="low"
                    )
                ],
                ticket=None,
                status="approved",
                confidence=0.95,
                time_estimate="As per SOP",
                fallback=True
            )
        
        # Partnership/strategy
        if "partnership" in task or "partner" in task or "strategy" in task:
            return ClubCoreLLMResponse(
                layers=[
                    Layer(name="strategic", status="evaluation"),
                    Layer(name="management", status="required")
                ],
                recommendation=[
                    Recommendation(
                        action="Prepare partnership proposal",
                        reason="Strategic decision requires documentation",
                        priority="medium"
                    ),
                    Recommendation(
                        action="Schedule management review",
                        reason="Executive approval required",
                        priority="high"
                    )
                ],
                ticket=Ticket(
                    title="Strategic Initiative Review",
                    description=task_data.get("task", "Partnership/strategy proposal"),
                    priority="medium",
                    tags=["strategic", "management", "review"]
                ),
                status="review_required",
                confidence=0.7,
                time_estimate="1-2 weeks",
                fallback=True
            )
        
        # Default general task
        return ClubCoreLLMResponse(
            layers=[Layer(name="general", status="active")],
            recommendation=[
                Recommendation(
                    action="Process using standard workflow",
                    reason="No specific protocol identified"
                )
            ],
            ticket=None,
            status="approved",
            confidence=0.5,
            time_estimate="Variable",
            fallback=True
        )
