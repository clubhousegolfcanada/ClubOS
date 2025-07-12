
from datetime import datetime
import re
from database import SessionLocal, Equipment, Procedure, IncidentLog
from knowledge_base import CLUBHOUSE_KNOWLEDGE


# Modular Detection
class DetectionRule:
    def detect(self, text: str) -> dict:
        raise NotImplementedError


class EquipmentIssueRule(DetectionRule):
    def detect(self, text):
        if any(k in text for k in ["broken", "error", "not working"]):
            return {"type": "equipment_issue"}
        return None


class EmergencyRule(DetectionRule):
    def detect(self, text):
        if any(k in text for k in ["emergency", "urgent", "power"]):
            return {"type": "emergency"}
        return None


class ProcedureRule(DetectionRule):
    def detect(self, text):
        if any(k in text for k in ["how to", "procedure", "close", "open"]):
            return {"type": "procedure"}
        return None


class DetectionEngine:
    def __init__(self):
        self.rules = [EquipmentIssueRule(), EmergencyRule(), ProcedureRule()]

    def analyze(self, task_text):
        task_lower = task_text.lower()
        for rule in self.rules:
            result = rule.detect(task_lower)
            if result:
                return {
                    **result,
                    "text": task_text,
                    "equipment": self._extract_equipment(task_lower),
                    "location": self._extract_location(task_lower)
                }
        return {
            "type": "general",
            "text": task_text,
            "equipment": self._extract_equipment(task_lower),
            "location": self._extract_location(task_lower)
        }

    def _extract_equipment(self, text):
        return [e for e in ["trackman", "projector", "simulator"] if e in text]

    def _extract_location(self, text):
        match = re.search(r"bay\s*(\d+)", text)
        return f"bay_{match.group(1)}" if match else None


# ClubOps: Procedural Logic
class ClubOpsEngine:
    def __init__(self, procedures):
        self.procedures = procedures

    def get(self, text):
        text_lower = text.lower()
        if "close" in text_lower:
            return self.procedures.get("closing", {})
        elif "open" in text_lower:
            return self.procedures.get("opening", {})
        return {"steps": ["Procedure not found. Contact manager."]}


# Ticket Engine: Logging Layer
class TicketLogger:
    def __init__(self):
        self.db = SessionLocal()

    def log(self, context, response):
        print(f"[LOGGED] Type={context['type']} | Equip={context['equipment']} | Loc={context['location']}")
        print(f"[RESOLUTION] {response.get('recommendation')}")
        # future: self.db.add(IncidentLog(...))


# ClubCore: Central Processor
class OperationalEngine:
    def __init__(self):
        self.knowledge = CLUBHOUSE_KNOWLEDGE
        self.detector = DetectionEngine()
        self.ops = ClubOpsEngine(self.knowledge.get("procedures", {}))
        self.logger = TicketLogger()

    async def process_request(self, request):
        context = self.detector.analyze(request['task'])

        if context["type"] == "equipment_issue":
            solution = self._get_equipment_solution(context)
        elif context["type"] == "emergency":
            solution = self._get_emergency_response(context)
        elif context["type"] == "procedure":
            solution = self.ops.get(context["text"])
        else:
            solution = {"response": "Please be more specific about the issue."}

        response = {
            "status": "completed",
            "confidence": 0.95,
            "recommendation": solution.get("steps", ["No specific steps found"]),
            "time_estimate": solution.get("time", "Unknown"),
            "contact_if_fails": solution.get("contact", "Manager")
        }

        self.logger.log(context, response)
        return response

    def _get_equipment_solution(self, context):
        for issue, solution in self.knowledge.get("equipment_troubleshooting", {}).items():
            if any(word in context["text"].lower() for word in issue.split("_")):
                return solution
        return {
            "steps": [
                "1. Power cycle the equipment",
                "2. Check all connections",
                "3. Contact technical support"
            ],
            "time": "10 minutes",
            "contact": "Tech Support"
        }

    def _get_emergency_response(self, context):
        if "power" in context["text"].lower():
            return self.knowledge.get("emergency_procedures", {}).get("power_outage", {})
        return {
            "steps": [
                "1. Ensure safety",
                "2. Contact manager",
                "3. Document issue"
            ]
        }
