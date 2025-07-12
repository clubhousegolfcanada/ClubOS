# backend/core/prompt.py
from typing import Dict, Any
import json

class PromptBuilder:
    @staticmethod
    def build_system_prompt() -> str:
        return """You are ClubCore AI, an operational assistant for Clubhouse 24/7 Golf facilities.
        
Your role is to analyze operational tasks and provide structured recommendations.

You must respond with valid JSON containing:
- layers: Array of system layers involved (e.g., "pricing", "inventory", "scheduling", "equipment", "facilities")
- recommendation: Array of action items with reasons
- ticket: Optional support ticket if issue requires escalation
- status: "approved", "rejected", or "review_required"
- confidence: Float between 0-1
- time_estimate: Estimated completion time (e.g., "15 minutes", "2 hours")

Example response:
{
    "layers": [
        {"name": "pricing", "status": "violation", "details": "Exceeds cap"}
    ],
    "recommendation": [
        {"action": "Adjust pricing to $35/hr", "reason": "Corporate cap exceeded", "priority": "high"}
    ],
    "ticket": {
        "title": "Pricing violation detected",
        "description": "Bay pricing exceeds corporate maximum",
        "priority": "high",
        "tags": ["pricing", "compliance"]
    },
    "status": "review_required",
    "confidence": 0.95,
    "time_estimate": "5 minutes"
}

Guidelines:
- For equipment issues (TrackMan, projectors), always generate a ticket
- For pricing over $35/hr, flag as violation and require review
- For installations, estimate 2-4 hours
- For SOPs, reference standard procedures
- For partnerships, require management approval"""

    @staticmethod
    def build_task_prompt(
        task: str,
        priority: str,
        operation: str,
        toggles: Dict[str, bool],
        context: Dict[str, Any]
    ) -> str:
        # Handle specific scenarios
        price_info = ""
        if "pricing" in task.lower() or "price" in task.lower():
            current_price = context.get("current_price", 0)
            if current_price > 35:
                price_info = f"\nIMPORTANT: Current price ${current_price}/hr exceeds corporate cap of $35/hr"
        
        equipment_info = ""
        if any(equip in task.lower() for equip in ["trackman", "projector", "simulator", "bay"]):
            equipment_info = "\nNOTE: Equipment issues require immediate ticket generation for technical support"
        
        location_info = ""
        if context.get("location"):
            location_info = f"\nLocation: {context['location']}"
        
        prompt = f"""Analyze this operational task for Clubhouse 24/7 Golf:

Task: {task}
Priority: {priority}
Operation Type: {operation}
Active Features: {json.dumps(toggles, indent=2)}
Context: {json.dumps(context, indent=2)}
{location_info}
{price_info}
{equipment_info}

Based on this information:
1. Identify which system layers are involved
2. Provide specific actionable recommendations
3. Determine if a ticket should be generated
4. Assess the overall status and your confidence level
5. Estimate time to completion

Provide your analysis and recommendations in the required JSON format."""
        
        return prompt
