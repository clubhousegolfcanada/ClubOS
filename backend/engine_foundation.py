"""
ClubOS Engine Foundation
Modular cognitive processing system with layered architecture
"""

from datetime import datetime
import re
import time
from database import SessionLocal, Equipment, Procedure, IncidentLog, TaskHistory
from schemas import TaskResult
from knowledge_base import CLUBHOUSE_KNOWLEDGE

# Import ticket system after models are defined
try:
    from ticket_system import TicketEngine
except ImportError:
    print("⚠️  ticket_system module not found - tickets disabled")
    TicketEngine = None

# ========================================
# LAYER 1: CAPABILITY FRONTIER
# ========================================

class CapabilityFrontierRule:
    """Base class for capability boundary rules"""
    def check(self, request: dict) -> dict:
        raise NotImplementedError

class PricingRule(CapabilityFrontierRule):
    """Enforce pricing boundaries"""
    def check(self, request):
        task = request.get('task', '').lower()
        
        # Check for pricing requests above limit
        if 'price' in task or 'cost' in task:
            # Extract dollar amounts
            amounts = re.findall(r'\$(\d+)', task)
            for amount in amounts:
                if int(amount) > 35:
                    return {
                        "blocked": True,
                        "reason": f"Pricing request ${amount} exceeds maximum allowed ${35}",
                        "recommendation": "Contact management for pricing above $35/hour"
                    }
        
        return {"blocked": False}

class ContentRule(CapabilityFrontierRule):
    """Content and tone restrictions"""
    def check(self, request):
        task = request.get('task', '').lower()
        
        # Block requests for prohibited content
        prohibited = ['off-white', 'corporate tone', 'dynamic pricing']
        for item in prohibited:
            if item in task:
                return {
                    "blocked": True, 
                    "reason": f"Request contains prohibited element: {item}",
                    "recommendation": "Refer to brand guidelines for approved alternatives"
                }
        
        return {"blocked": False}

class CapabilityFrontier:
    """Guardrail layer - enforces system boundaries"""
    
    def __init__(self):
        self.rules = [PricingRule(), ContentRule()]
    
    def process(self, request):
        print("🛡️  [CapabilityFrontier] Checking boundaries...")
        
        for rule in self.rules:
            result = rule.check(request)
            if result.get("blocked"):
                print(f"🚫 [CapabilityFrontier] Blocked: {result['reason']}")
                return {
                    "status": "blocked",
                    "layer": "CapabilityFrontier",
                    "reason": result["reason"],
                    "recommendation": [result["recommendation"]]
                }
        
        print("✅ [CapabilityFrontier] Request cleared")
        return {"status": "approved", "layer": "CapabilityFrontier"}

# ========================================
# LAYER 2: CLUBOPS - PROCEDURAL LOGIC
# ========================================

class DetectionRule:
    """Base class for task detection"""
    def detect(self, text: str) -> dict:
        raise NotImplementedError

class EquipmentIssueRule(DetectionRule):
    def detect(self, text):
        equipment_terms = ["trackman", "projector", "simulator", "screen"]
        issue_terms = ["broken", "error", "not working", "no image", "black screen", "not reading"]
        
        if any(eq in text for eq in equipment_terms) and any(issue in text for issue in issue_terms):
            return {"type": "equipment_issue", "confidence": 0.9}
        return None

class EmergencyRule(DetectionRule):
    def detect(self, text):
        emergency_terms = ["emergency", "urgent", "power outage", "fire", "flood", "safety"]
        if any(term in text for term in emergency_terms):
            return {"type": "emergency", "confidence": 0.95}
        return None

class ProcedureRule(DetectionRule):
    def detect(self, text):
        procedure_terms = ["how to", "procedure", "close", "open", "checklist"]
        if any(term in text for term in procedure_terms):
            return {"type": "procedure", "confidence": 0.8}
        return None

class ClubOpsEngine:
    """Procedural knowledge and muscle memory"""
    
    def __init__(self):
        self.knowledge = CLUBHOUSE_KNOWLEDGE
        self.detection_rules = [EquipmentIssueRule(), EmergencyRule(), ProcedureRule()]
    
    def analyze_task(self, task_text):
        """Analyze and categorize the task"""
        task_lower = task_text.lower()
        
        # Run detection rules
        for rule in self.detection_rules:
            result = rule.detect(task_lower)
            if result:
                return {
                    **result,
                    "text": task_text,
                    "equipment": self._extract_equipment(task_lower),
                    "location": self._extract_location(task_lower),
                    "bay": self._extract_bay(task_lower)
                }
        
        return {
            "type": "general",
            "text": task_text,
            "equipment": self._extract_equipment(task_lower),
            "location": self._extract_location(task_lower),
            "bay": self._extract_bay(task_lower),
            "confidence": 0.5
        }
    
    def _extract_equipment(self, text):
        equipment_types = ["trackman", "projector", "simulator", "screen"]
        return [eq for eq in equipment_types if eq in text]
    
    def _extract_location(self, text):
        locations = ["river oaks", "dartmouth", "downtown", "memorial", "woodlands"]
        for loc in locations:
            if loc in text:
                return loc.title()
        return None
    
    def _extract_bay(self, text):
        match = re.search(r"bay\s*(\d+)", text)
        return int(match.group(1)) if match else None
    
    def get_solution(self, context):
        """Get procedural solution based on context"""
        if context["type"] == "equipment_issue":
            return self._get_equipment_solution(context)
        elif context["type"] == "emergency":
            return self._get_emergency_response(context)
        elif context["type"] == "procedure":
            return self._get_procedure_steps(context)
        else:
            return self._get_general_response(context)
    
    def _get_equipment_solution(self, context):
        equipment_kb = self.knowledge.get("equipment_troubleshooting", {})
        
        # Try to match specific equipment issues
        for issue_key, solution in equipment_kb.items():
            if any(word in context["text"].lower() for word in issue_key.split("_")):
                return solution
        
        # Generic equipment troubleshooting
        return {
            "steps": [
                "1. Power cycle the equipment (hold power button 10 seconds)",
                "2. Check all cable connections",
                "3. Clean any sensors or lenses",
                "4. Restart associated computer/software",
                "5. Contact technical support if issue persists"
            ],
            "time": "10-15 minutes",
            "contact": "Technical Support"
        }
    
    def _get_emergency_response(self, context):
        emergency_kb = self.knowledge.get("emergency_procedures", {})
        
        if "power" in context["text"].lower():
            return emergency_kb.get("power_outage", {})
        
        return {
            "steps": [
                "1. Ensure immediate safety of staff and customers",
                "2. Contact emergency services if needed (911)",
                "3. Notify management immediately",
                "4. Document the incident",
                "5. Follow up with detailed report"
            ],
            "time": "Immediate",
            "contact": "Emergency Services / Management"
        }
    
    def _get_procedure_steps(self, context):
        procedures_kb = self.knowledge.get("procedures", {})
        
        if "open" in context["text"].lower():
            return procedures_kb.get("opening", {})
        elif "close" in context["text"].lower():
            return procedures_kb.get("closing", {})
        
        return {
            "steps": ["1. Refer to standard operating procedures manual", "2. Contact manager for guidance"],
            "time": "Variable",
            "contact": "Manager"
        }
    
    def _get_general_response(self, context):
        return {
            "steps": [
                "1. Gather more specific information about the issue",
                "2. Check relevant documentation or procedures",
                "3. Escalate to appropriate staff member",
                "4. Document any actions taken"
            ],
            "time": "5-10 minutes",
            "contact": "Manager"
        }

# ========================================
# LAYER 3: SIGNALOS - STRATEGIC ENGINE
# ========================================

class SignalOSEngine:
    """Strategic planning and decision making"""
    
    def enhance_response(self, context, solution):
        """Add strategic insights to the response"""
        enhanced = solution.copy()
        
        # Add priority assessment
        enhanced["priority"] = self._assess_priority(context)
        
        # Add resource requirements
        enhanced["resources"] = self._identify_resources(context)
        
        # Add prevention recommendations
        enhanced["prevention"] = self._suggest_prevention(context)
        
        return enhanced
    
    def _assess_priority(self, context):
        """Assess task priority based on impact and urgency"""
        score = 0
        
        # Equipment failures are high priority
        if context["type"] == "equipment_issue":
            score += 3
        
        # Emergencies are critical
        if context["type"] == "emergency":
            score += 5
        
        # Multiple equipment affected
        if len(context.get("equipment", [])) > 1:
            score += 2
        
        # Bay-specific issues affect revenue
        if context.get("bay"):
            score += 2
        
        if score >= 5:
            return "critical"
        elif score >= 3:
            return "high" 
        elif score >= 1:
            return "medium"
        else:
            return "low"
    
    def _identify_resources(self, context):
        """Identify required resources"""
        resources = []
        
        if context["type"] == "equipment_issue":
            resources.extend(["Technical staff", "Replacement parts", "Tools"])
        
        if context.get("bay"):
            resources.append("Bay downtime coordination")
        
        return resources
    
    def _suggest_prevention(self, context):
        """Suggest preventive measures"""
        if context["type"] == "equipment_issue":
            return ["Schedule regular maintenance", "Update equipment monitoring", "Staff training on early detection"]
        
        return ["Review procedures", "Consider process improvements"]

# ========================================
# LAYER 4: CLUBHOST - PERSONALITY FILTER  
# ========================================

class ClubhostEngine:
    """Personality and tone enforcement"""
    
    def apply_tone(self, response):
        """Apply Clubhost personality to response"""
        # Convert technical language to direct, practical language
        filtered_steps = []
        
        for step in response.get("steps", []):
            # Remove unnecessary politeness and corporate speak
            filtered_step = step.replace("Please ", "").replace("kindly ", "")
            filtered_step = self._make_direct(filtered_step)
            filtered_steps.append(filtered_step)
        
        response["steps"] = filtered_steps
        
        # Add direct contact info
        if response.get("contact"):
            response["contact_direct"] = f"Call {response['contact']} immediately if steps don't work"
        
        return response
    
    def _make_direct(self, text):
        """Make language more direct and actionable"""
        # Replace vague terms with specific actions
        replacements = {
            "check if": "verify that",
            "try to": "",
            "attempt to": "",
            "consider": "",
            "you might want to": "",
            "it would be good to": ""
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()

# ========================================
# LAYER 5: TICKET ENGINE
# ========================================

class TicketLogger:
    """Ticket creation and logging layer"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.ticket_engine = TicketEngine() if TicketEngine else None
    
    def log_and_ticket(self, context, response, form_data=None):
        """Log the incident and create ticket if needed"""
        
        # Log to incident table
        incident = IncidentLog(
            issue_description=context["text"],
            location=context.get("location"),
            issue_category=context["type"],
            priority=response.get("priority", "medium"),
            confidence_score=context.get("confidence", 0.8),
            status="open"
        )
        
        self.db.add(incident)
        self.db.commit()
        
        # Create ticket if ticket engine available and requested
        ticket_data = None
        if self.ticket_engine and form_data and form_data.get('generate_ticket', False):
            try:
                task_result = {
                    "task": context["text"],
                    "recommendation": response.get("steps", [])
                }
                ticket_data = self.ticket_engine.create_ticket(task_result, form_data)
                
                # Link ticket to incident
                incident.status = "assigned"
                self.db.commit()
                
            except Exception as e:
                print(f"❌ Ticket creation failed: {e}")
        
        self.db.close()
        return ticket_data

# ========================================
# MAIN OPERATIONAL ENGINE
# ========================================

class OperationalEngine:
    """Main engine coordinating all layers"""
    
    def __init__(self):
        self.capability_frontier = CapabilityFrontier()
        self.clubops = ClubOpsEngine()
        self.signalos = SignalOSEngine()
        self.clubhost = ClubhostEngine()
        self.ticket_logger = TicketLogger()
    
    async def process_request(self, request: dict) -> dict:
        """Process request through all cognitive layers"""
        start_time = time.time()
        
        print(f"🧠 [Engine] Processing: {request.get('task', '')[:50]}...")
        
        # Layer 1: Capability Frontier
        boundary_check = self.capability_frontier.process(request)
        if boundary_check.get("status") == "blocked":
            return self._format_blocked_response(boundary_check)
        
        # Layer 2: ClubOps Analysis
        print("⚙️  [ClubOps] Analyzing task...")
        context = self.clubops.analyze_task(request['task'])
        solution = self.clubops.get_solution(context)
        
        # Layer 3: SignalOS Enhancement
        print("🎯 [SignalOS] Adding strategic insights...")
        enhanced_solution = self.signalos.enhance_response(context, solution)
        
        # Layer 4: Clubhost Tone
        print("🗣️  [Clubhost] Applying personality filter...")
        final_response = self.clubhost.apply_tone(enhanced_solution)
        
        # Layer 5: Ticket Logging
        print("📝 [TicketEngine] Logging incident...")
        ticket_data = self.ticket_logger.log_and_ticket(
            context, 
            final_response, 
            request.get('form_data')
        )
        
        processing_time = time.time() - start_time
        
        # Format final response
        response = {
            "status": "completed",
            "confidence": context.get("confidence", 0.8),
            "recommendation": final_response.get("steps", ["No specific steps available"]),
            "time_estimate": final_response.get("time", "Unknown"),
            "contact_if_fails": final_response.get("contact", "Manager"),
            "priority": final_response.get("priority", "medium"),
            "category": context["type"],
            "processing_time": round(processing_time, 2),
            "layers_processed": ["CapabilityFrontier", "ClubOps", "SignalOS", "Clubhost", "TicketEngine"]
        }
        
        if ticket_data:
            response["ticket_created"] = ticket_data["id"]
        
        print(f"✅ [Engine] Processing complete in {processing_time:.2f}s")
        return response
    
    def _format_blocked_response(self, boundary_check):
        """Format response for blocked requests"""
        return {
            "status": "blocked",
            "confidence": 1.0,
            "recommendation": boundary_check["recommendation"],
            "time_estimate": "N/A",
            "contact_if_fails": "Management",
            "priority": "blocked",
            "category": "policy_violation",
            "reason": boundary_check["reason"]
        }
