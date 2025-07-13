# backend/core/enhanced_sop_resolver.py
"""
Enhanced SOP Resolver that combines existing Google Drive sync with action execution
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import the existing Google Drive service from paste.txt
from backend.core.google_drive_sop_service import GoogleDriveSOPService, SOPAwareEngine
from backend.core.action_handler import ActionHandler
from backend.core.clubhost_tone import ClubhostTone
from backend.schemas import ClubCoreLLMResponse, Layer, Recommendation, Ticket
from backend.database import SessionLocal
from backend.ticket_system import TicketSystem

logger = logging.getLogger(__name__)

class EnhancedSOPResolver:
    """
    Combines existing Google Drive SOP sync with automated execution.
    Uses the caching from paste.txt but adds execution capabilities.
    """
    
    def __init__(self):
        # Use existing services
        self.sop_engine = SOPAwareEngine()
        self.action_handler = ActionHandler()
        self.ticket_system = TicketSystem()
    
    async def resolve(
        self, 
        issue_description: str, 
        context: Optional[Dict[str, Any]] = None,
        auto_execute: bool = True
    ) -> ClubCoreLLMResponse:
        """
        Resolve issue using cached SOPs with optional auto-execution.
        """
        context = context or {}
        
        # Get SOP guidance using existing search
        sop_guidance = await self.sop_engine.get_sop_guidance(issue_description)
        
        if sop_guidance["status"] == "no_sops_found":
            # No SOP found - create escalation ticket
            return self._create_no_sop_response(issue_description, context)
        
        # Found SOP - prepare for execution
        sop_title = sop_guidance["title"]
        sop_steps = sop_guidance["steps"]
        
        if not auto_execute:
            # Just return the SOP without executing
            return self._create_sop_reference_response(sop_guidance, issue_description)
        
        # Execute SOP steps
        execution_results = []
        layers_involved = set(["sop", "operations"])
        
        for idx, step in enumerate(sop_steps):
            if not step.strip():
                continue
                
            # Analyze step for actions
            step_analysis = self._analyze_step(step)
            
            # Add involved layers
            layers_involved.update(step_analysis["layers"])
            
            # Execute if action identified
            if step_analysis["action"] != "generic_step":
                try:
                    result = await self.action_handler.handle(
                        action_type=step_analysis["action"],
                        context={
                            **context,
                            "step": step,
                            "step_number": idx + 1,
                            "sop_title": sop_title
                        }
                    )
                    execution_results.append({
                        "step": idx + 1,
                        "action": step_analysis["action"],
                        "success": result.get("success", False),
                        "result": result
                    })
                except Exception as e:
                    logger.error(f"Step {idx + 1} execution failed: {e}")
                    execution_results.append({
                        "step": idx + 1,
                        "action": step_analysis["action"],
                        "success": False,
                        "error": str(e)
                    })
        
        # Build response
        return self._create_execution_response(
            sop_guidance,
            execution_results,
            list(layers_involved),
            issue_description
        )
    
    def _analyze_step(self, step: str) -> Dict[str, Any]:
        """
        Analyze SOP step to identify action type and metadata.
        """
        step_lower = step.lower()
        
        # Identify action type
        if "refund" in step_lower:
            action = "refund"
            layers = ["financial"]
        elif any(word in step_lower for word in ["call", "contact", "email", "notify"]):
            action = "contact_customer"
            layers = ["customer_service"]
        elif any(word in step_lower for word in ["restart", "reboot", "power"]):
            action = "equipment_restart"
            layers = ["equipment", "facilities"]
        elif any(word in step_lower for word in ["check", "verify", "confirm"]):
            action = "verification"
            layers = ["quality_control"]
        else:
            action = "generic_step"
            layers = ["operations"]
        
        return {
            "action": action,
            "layers": layers,
            "critical": any(word in step_lower for word in ["must", "critical", "essential"])
        }
    
    def _create_no_sop_response(self, issue: str, context: Dict[str, Any]) -> ClubCoreLLMResponse:
        """
        Create response when no SOP is found.
        """
        # Create escalation ticket
        db = SessionLocal()
        try:
            ticket = self.ticket_system.create_ticket(
                db=db,
                title=f"No SOP Available: {issue[:50]}",
                description=f"Issue reported without existing SOP:\n{issue}\n\nContext: {context}",
                priority="medium",
                tags=["no-sop", "documentation-needed", "manual-resolution"]
            )
            ticket_id = str(ticket.id)
        finally:
            db.close()
        
        return ClubCoreLLMResponse(
            layers=[Layer(name="escalation", status="required")],
            recommendation=[
                Recommendation(
                    action="Create SOP for this issue type",
                    reason="No existing procedure found",
                    priority="medium"
                ),
                Recommendation(
                    action="Handle manually per staff judgment",
                    reason="Automated resolution unavailable",
                    priority="high"
                )
            ],
            ticket=Ticket(
                id=ticket_id,
                title=f"Manual Resolution Required",
                description=f"No SOP found for: {issue}",
                priority="medium",
                tags=["manual", "no-sop"]
            ),
            status="review_required",
            confidence=0.3,
            time_estimate="Manual review required",
            fallback=True
        )
    
    def _create_sop_reference_response(self, sop_guidance: Dict, issue: str) -> ClubCoreLLMResponse:
        """
        Create response that references SOP without executing.
        """
        return ClubCoreLLMResponse(
            layers=[Layer(name="sop", status="found")],
            recommendation=[
                Recommendation(
                    action=f"Follow SOP: {sop_guidance['title']}",
                    reason=f"Relevance score: {sop_guidance['relevance_score']}",
                    priority="high"
                )
            ],
            ticket=None,
            status="approved",
            confidence=0.9,
            time_estimate=f"{len(sop_guidance['steps'])} steps",
            metadata={
                "sop_title": sop_guidance["title"],
                "sop_link": sop_guidance["drive_link"],
                "steps": sop_guidance["steps"]
            }
        )
    
    def _create_execution_response(
        self,
        sop_guidance: Dict,
        execution_results: List[Dict],
        layers: List[str],
        issue: str
    ) -> ClubCoreLLMResponse:
        """
        Create response after executing SOP steps.
        """
        # Calculate success rate
        total_executed = len(execution_results)
        successful = sum(1 for r in execution_results if r.get("success", False))
        success_rate = successful / total_executed if total_executed > 0 else 0
        
        # Determine status
        if success_rate == 1.0:
            status = "approved"
        elif success_rate >= 0.5:
            status = "review_required"
        else:
            status = "rejected"
        
        # Build recommendations
        recommendations = []
        if success_rate < 1.0:
            failed_steps = [r for r in execution_results if not r.get("success", False)]
            for failed in failed_steps:
                recommendations.append(
                    Recommendation(
                        action=f"Manually complete step {failed['step']}",
                        reason=f"Automated execution failed: {failed.get('error', 'Unknown error')}",
                        priority="high"
                    )
                )
        
        # Create ticket if needed
        ticket = None
        if success_rate < 1.0:
            db = SessionLocal()
            try:
                ticket_obj = self.ticket_system.create_ticket(
                    db=db,
                    title=f"SOP Partial Execution: {sop_guidance['title'][:30]}",
                    description=self._format_execution_summary(sop_guidance, execution_results),
                    priority="medium" if success_rate >= 0.5 else "high",
                    tags=["sop-execution", "partial-success"]
                )
                ticket = Ticket(
                    id=str(ticket_obj.id),
                    title=ticket_obj.title,
                    description=ticket_obj.description,
                    priority=ticket_obj.priority,
                    tags=["sop-execution"]
                )
            finally:
                db.close()
        
        # Apply Clubhouse tone
        summary = ClubhostTone.create_operational_summary(
            task=issue,
            status=status,
            layers=layers
        )
        
        return ClubCoreLLMResponse(
            layers=[Layer(name=l, status="active") for l in layers],
            recommendation=recommendations if recommendations else [
                Recommendation(
                    action="SOP executed successfully",
                    reason=f"All {total_executed} steps completed",
                    priority="low"
                )
            ],
            ticket=ticket,
            status=status,
            confidence=success_rate,
            time_estimate=f"{total_executed} steps executed",
            metadata={
                "sop_title": sop_guidance["title"],
                "sop_link": sop_guidance["drive_link"],
                "execution_summary": summary,
                "success_rate": success_rate
            }
        )
    
    def _format_execution_summary(self, sop_guidance: Dict, results: List[Dict]) -> str:
        """
        Format execution results for ticket description.
        """
        lines = [
            f"SOP: {sop_guidance['title']}",
            f"Drive Link: {sop_guidance['drive_link']}",
            "",
            "EXECUTION RESULTS:"
        ]
        
        for result in results:
            status = "✓" if result.get("success") else "✗"
            lines.append(
                f"{status} Step {result['step']}: {result['action']} - "
                f"{'Success' if result.get('success') else result.get('error', 'Failed')}"
            )
        
        return "\n".join(lines)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current Google Drive sync status.
        """
        return self.sop_engine.drive_service.get_cache_status()
    
    def refresh_sops(self) -> Dict[str, Any]:
        """
        Manually refresh SOP cache from Google Drive.
        """
        return self.sop_engine.refresh_sops()
