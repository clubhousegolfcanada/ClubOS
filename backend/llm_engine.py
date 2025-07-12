"""
Advanced LLM Engine for ClubOS
Uses OpenAI's latest models for intelligent reasoning and decision making
"""

import os
import json
from typing import Dict, List, Optional
from openai import OpenAI
from datetime import datetime
import asyncio

class AdvancedLLMEngine:
    """Advanced LLM engine with context-aware reasoning"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4-1106-preview"  # Latest GPT-4 Turbo
        self.facility_context = self.load_facility_context()
        
    def load_facility_context(self) -> Dict:
        """Load facility-specific context"""
        return {
            "facility_type": "24/7 Autonomous Golf Simulator Facility",
            "operating_model": "Unmanned operation with smart systems",
            "bay_count": 8,
            "equipment": {
                "trackman": "TrackMan 4 units in each bay",
                "projectors": "Epson Pro L1755U projectors",
                "simulators": "Custom golf simulation software",
                "access_control": "Smart lock system with mobile app",
                "hvac": "Automated climate control",
                "lighting": "Smart LED lighting system"
            },
            "customer_interaction": "Self-service with AI assistance",
            "business_hours": "24/7 operation",
            "maintenance_model": "Predictive maintenance with remote monitoring"
        }
    
    async def analyze_issue_with_context(self, issue_description: str, 
                                       sop_context: Optional[Dict] = None,
                                       phone_context: Optional[Dict] = None) -> Dict:
        """Analyze issue with full context from SOPs and phone data"""
        
        # Build comprehensive context
        context_prompt = self.build_context_prompt(issue_description, sop_context, phone_context)
        
        messages = [
            {
                "role": "system",
                "content": f"""You are ClubOS, an AI system managing a 24/7 autonomous golf simulator facility. 

FACILITY CONTEXT:
{json.dumps(self.facility_context, indent=2)}

YOUR ROLE:
- Provide immediate, actionable solutions for facility issues
- Consider the unmanned nature of the facility
- Prioritize customer experience and safety
- Leverage automation and smart systems
- Escalate only when remote resolution isn't possible

RESPONSE FORMAT:
Always respond with a JSON object containing:
- "analysis": Brief analysis of the issue
- "category": Issue category (equipment/access/facility/customer/emergency)
- "severity": 1-5 scale (1=minor, 5=critical)
- "immediate_actions": List of immediate automated actions to take
- "customer_communication": Message to send to affected customers
- "resolution_steps": Detailed step-by-step resolution
- "estimated_time": Expected resolution time
- "escalation_needed": Boolean if human intervention required
- "prevention": Future prevention recommendations
- "confidence": 0-1 confidence in solution
"""
            },
            {
                "role": "user", 
                "content": context_prompt
            }
        ]
        
        try:
            response = await self.call_openai_async(messages)
            
            # Parse JSON response
            result = json.loads(response)
            
            # Add metadata
            result.update({
                "llm_model": self.model,
                "analysis_time": datetime.now().isoformat(),
                "context_sources": {
                    "sop_available": sop_context is not None,
                    "phone_data_available": phone_context is not None
                }
            })
            
            return result
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "analysis": "LLM analysis failed - JSON parse error",
                "category": "system_error",
                "severity": 3,
                "immediate_actions": ["Log error for manual review"],
                "customer_communication": "We're aware of the issue and working on a solution.",
                "resolution_steps": ["Manual review required"],
                "estimated_time": "Unknown",
                "escalation_needed": True,
                "prevention": ["Improve LLM response formatting"],
                "confidence": 0.0,
                "error": "JSON parsing failed"
            }
            
        except Exception as e:
            return {
                "analysis": f"LLM analysis failed: {str(e)}",
                "category": "system_error", 
                "severity": 3,
                "immediate_actions": ["Log error for manual review"],
                "customer_communication": "We're experiencing a temporary system issue.",
                "resolution_steps": ["Manual review required"],
                "estimated_time": "Unknown",
                "escalation_needed": True,
                "prevention": ["Debug LLM integration"],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def build_context_prompt(self, issue_description: str, 
                           sop_context: Optional[Dict] = None,
                           phone_context: Optional[Dict] = None) -> str:
        """Build comprehensive context prompt"""
        
        prompt_parts = [
            f"CURRENT ISSUE: {issue_description}",
            ""
        ]
        
        # Add SOP context if available
        if sop_context and sop_context.get('status') == 'sop_found':
            prompt_parts.extend([
                "RELEVANT SOP DOCUMENTATION:",
                f"Title: {sop_context['title']}",
                f"Steps from SOP:",
            ])
            for i, step in enumerate(sop_context.get('steps', [])[:5], 1):
                prompt_parts.append(f"{i}. {step}")
            prompt_parts.extend([
                f"Equipment mentioned: {', '.join(sop_context.get('equipment', []))}",
                f"SOP Link: {sop_context.get('drive_link', 'N/A')}",
                ""
            ])
        
        # Add phone context if available
        if phone_context and phone_context.get('status') == 'found_similar_issues':
            prompt_parts.extend([
                "RECENT CUSTOMER REPORTS:",
                f"Similar issues reported: {phone_context['similar_count']}",
                "Customer descriptions:"
            ])
            for desc in phone_context.get('customer_descriptions', []):
                prompt_parts.append(f"- \"{desc}\"")
            prompt_parts.extend([
                f"Trending issues: {phone_context.get('trending_issues', {})}",
                ""
            ])
        
        prompt_parts.extend([
            "REQUIREMENTS:",
            "1. Provide immediate automated solution if possible",
            "2. Consider this is an unmanned facility - no staff on site", 
            "3. Prioritize customer safety and experience",
            "4. Use smart systems and automation where possible",
            "5. Provide clear customer communication",
            "6. Only escalate if remote resolution is impossible",
            "",
            "Analyze this issue and provide your response in the specified JSON format."
        ])
        
        return "\n".join(prompt_parts)
    
    async def call_openai_async(self, messages: List[Dict]) -> str:
        """Make async call to OpenAI API"""
        
        # Use asyncio to run the synchronous OpenAI call
        loop = asyncio.get_event_loop()
        
        def make_call():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Low temperature for consistent responses
                max_tokens=1500,
                timeout=30
            )
            return response.choices[0].message.content
        
        return await loop.run_in_executor(None, make_call)
    
    async def generate_customer_notification(self, issue_analysis: Dict, 
                                           customer_phone: Optional[str] = None) -> Dict:
        """Generate customer notification based on issue analysis"""
        
        if issue_analysis.get('severity', 0) < 3:
            # Minor issues - standard notification
            return {
                "method": "app_notification",
                "urgency": "normal",
                "message": issue_analysis.get('customer_communication', 'Issue detected and being resolved.'),
                "eta": issue_analysis.get('estimated_time', 'Soon')
            }
        else:
            # Major issues - multiple notification methods
            return {
                "method": "multi_channel",
                "urgency": "high", 
                "channels": ["app_notification", "sms", "email"],
                "message": issue_analysis.get('customer_communication'),
                "eta": issue_analysis.get('estimated_time'),
                "compensation": self.calculate_compensation(issue_analysis)
            }
    
    def calculate_compensation(self, issue_analysis: Dict) -> Optional[Dict]:
        """Calculate customer compensation for major issues"""
        severity = issue_analysis.get('severity', 0)
        estimated_time = issue_analysis.get('estimated_time', '')
        
        if severity >= 4:
            # Critical issues - full refund
            return {
                "type": "full_refund",
                "reason": "Critical facility issue affecting your experience"
            }
        elif severity >= 3 and any(word in estimated_time.lower() for word in ['hour', 'hours']):
            # Major issues taking >1 hour
            return {
                "type": "partial_refund", 
                "amount": "50%",
                "reason": "Extended downtime affecting your session"
            }
        elif severity >= 3:
            # Major but quick resolution
            return {
                "type": "credit",
                "amount": "30 minutes free play",
                "reason": "Inconvenience during your visit"
            }
        
        return None
    
    async def predict_future_issues(self, recent_issues: List[Dict]) -> Dict:
        """Use LLM to predict potential future issues"""
        
        if not recent_issues:
            return {"status": "no_data"}
        
        # Prepare issue history for analysis
        issue_summary = []
        for issue in recent_issues[-10:]:  # Last 10 issues
            issue_summary.append({
                "description": issue.get('description', ''),
                "category": issue.get('category', ''),
                "severity": issue.get('severity', 0),
                "timestamp": issue.get('timestamp', '')
            })
        
        messages = [
            {
                "role": "system",
                "content": """You are a predictive maintenance AI for a 24/7 golf simulator facility. 
                
Analyze recent issues to predict potential future problems. Consider:
- Equipment wear patterns
- Seasonal factors
- Usage patterns
- Common failure modes

Respond with JSON containing:
- "predictions": List of predicted issues with probability
- "prevention_actions": Recommended preventive actions
- "priority_equipment": Equipment needing attention
- "timeline": When issues might occur
"""
            },
            {
                "role": "user",
                "content": f"Recent facility issues:\n{json.dumps(issue_summary, indent=2)}\n\nPredict potential future issues and recommend prevention actions."
            }
        ]
        
        try:
            response = await self.call_openai_async(messages)
            return json.loads(response)
        except:
            return {"status": "prediction_failed"}
    
    async def optimize_facility_operations(self, performance_data: Dict) -> Dict:
        """Use LLM to suggest operational optimizations"""
        
        messages = [
            {
                "role": "system", 
                "content": """You are an operations optimization AI for a 24/7 autonomous golf facility.

Analyze performance data and suggest optimizations for:
- Customer experience
- Equipment utilization
- Energy efficiency
- Predictive maintenance
- Revenue optimization

Respond with JSON containing specific, actionable recommendations."""
            },
            {
                "role": "user",
                "content": f"Facility performance data:\n{json.dumps(performance_data, indent=2)}\n\nProvide optimization recommendations."
            }
        ]
        
        try:
            response = await self.call_openai_async(messages)
            return json.loads(response)
        except:
            return {"status": "optimization_failed"}

# Integration with main ClubOS engine
class AIEnhancedClubOS:
    """ClubOS with advanced AI capabilities"""
    
    def __init__(self):
        self.llm_engine = AdvancedLLMEngine()
    
    async def process_issue_with_ai(self, issue_description: str,
                                  sop_context: Optional[Dict] = None,
                                  phone_context: Optional[Dict] = None) -> Dict:
        """Process issue with full AI analysis"""
        
        # Get AI analysis
        ai_analysis = await self.llm_engine.analyze_issue_with_context(
            issue_description, sop_context, phone_context
        )
        
        # Execute immediate actions if confidence is high
        if ai_analysis.get('confidence', 0) > 0.8:
            execution_results = await self.execute_immediate_actions(
                ai_analysis.get('immediate_actions', [])
            )
            ai_analysis['execution_results'] = execution_results
        
        # Generate customer notifications
        if ai_analysis.get('severity', 0) >= 2:
            notification = await self.llm_engine.generate_customer_notification(ai_analysis)
            ai_analysis['customer_notification'] = notification
        
        return ai_analysis
    
    async def execute_immediate_actions(self, actions: List[str]) -> List[Dict]:
        """Execute immediate automated actions"""
        results = []
        
        for action in actions:
            try:
                if "reset" in action.lower():
                    result = await self.execute_equipment_reset(action)
                elif "unlock" in action.lower():
                    result = await self.execute_door_unlock(action)
                elif "adjust" in action.lower():
                    result = await self.execute_setting_adjustment(action)
                else:
                    result = {"action": action, "status": "logged", "message": "Action logged for manual execution"}
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    "action": action,
                    "status": "failed", 
                    "error": str(e)
                })
        
        return results
    
    async def execute_equipment_reset(self, action: str) -> Dict:
        """Execute equipment reset action"""
        # This would integrate with your facility's IoT systems
        return {
            "action": action,
            "status": "simulated",
            "message": "Equipment reset command would be sent to facility systems"
        }
    
    async def execute_door_unlock(self, action: str) -> Dict:
        """Execute door unlock action"""
        # This would integrate with your access control system
        return {
            "action": action,
            "status": "simulated", 
            "message": "Door unlock command would be sent to access control system"
        }
    
    async def execute_setting_adjustment(self, action: str) -> Dict:
        """Execute facility setting adjustment"""
        # This would integrate with your building automation systems
        return {
            "action": action,
            "status": "simulated",
            "message": "Setting adjustment would be applied to facility systems"
        }
