# backend/core/clubhost_tone.py
from typing import Dict, List, Any
import re

class ClubhostTone:
    """
    Clubhost: The personality filter layer.
    Enforces Clubhouse 24/7's communication style - direct, operational, no corporate fluff.
    """
    
    # Tone style definitions
    TONE_STYLES = {
        "default": """You are Clubhouse 24/7's operational system. Communicate like a sharp facility manager:
- Direct and actionable. No pleasantries.
- Technical precision. No ambiguity.
- Operational mindset. Focus on what needs doing.
- Brief. If it can be said in 5 words, don't use 10.
- No corporate speak. No "synergy" or "leverage" nonsense.""",
        
        "rewrite": """Rewrite in Clubhouse operational style:
- Strip ALL filler words and phrases
- Convert to imperative mood where possible
- Remove hedging language ("might", "perhaps", "maybe")
- Make it sound like a competent ops manager wrote it
- If there's a number, lead with it""",
        
        "technical": """Technical response mode:
- Specifications and metrics only
- No explanations unless failure-critical
- Use bullet points or numbered lists
- Include exact values, not approximations
- Format: [SYSTEM] - [STATUS] - [ACTION]""",
        
        "escalation": """Escalation communication style:
- ISSUE: [One line summary]
- IMPACT: [Operational impact]
- ACTION: [Required immediate action]
- OWNER: [Who needs to act]
- DEADLINE: [When]""",
        
        "sop": """Standard Operating Procedure style:
- Step-by-step numbered format
- Each step starts with a verb
- Include timing for each step
- Note safety/critical points with ⚠️
- End with verification step"""
    }
    
    # Phrases to eliminate
    FLUFF_PHRASES = [
        "I understand your",
        "I'd be happy to",
        "Let me help you with",
        "Thank you for",
        "Please feel free to",
        "If you have any questions",
        "Is there anything else",
        "I hope this helps",
        "Just to clarify",
        "As an AI assistant",
        "I appreciate your",
        "Would you like me to",
        "It seems like",
        "I think that",
        "In my opinion"
    ]
    
    # Corporate speak to operational speak
    REPLACEMENTS = {
        "leverage": "use",
        "utilize": "use",
        "implement": "do",
        "facilitate": "help",
        "optimize": "improve",
        "synergize": "work together",
        "ideate": "think",
        "circle back": "follow up",
        "touch base": "talk",
        "deep dive": "review",
        "bandwidth": "time",
        "deliverables": "work",
        "action items": "tasks",
        "going forward": "next",
        "at the end of the day": "",
        "low hanging fruit": "easy fixes",
        "move the needle": "make progress",
        "think outside the box": "try new approaches"
    }
    
    @classmethod
    def wrap_prompt(cls, prompt: str, style: str = "default") -> str:
        """
        Wrap a prompt with tone instructions.
        
        Args:
            prompt: The original prompt
            style: One of: default, rewrite, technical, escalation, sop
            
        Returns:
            Wrapped prompt with tone control
        """
        tone_instruction = cls.TONE_STYLES.get(style, cls.TONE_STYLES["default"])
        return f"{tone_instruction}\n\n{prompt}"
    
    @classmethod
    def format_response(cls, response: str, aggressive: bool = True) -> str:
        """
        Format a response to match Clubhouse tone.
        
        Args:
            response: The original response
            aggressive: If True, applies more aggressive filtering
            
        Returns:
            Formatted response
        """
        formatted = response
        
        # Remove fluff phrases
        for phrase in cls.FLUFF_PHRASES:
            formatted = re.sub(f"{phrase}[^.]*\.", "", formatted, flags=re.IGNORECASE)
            formatted = re.sub(f"{phrase}[^.]*,", "", formatted, flags=re.IGNORECASE)
        
        # Replace corporate speak
        for corporate, direct in cls.REPLACEMENTS.items():
            formatted = re.sub(rf"\b{corporate}\b", direct, formatted, flags=re.IGNORECASE)
        
        # Remove multiple spaces and clean up
        formatted = re.sub(r'\s+', ' ', formatted)
        formatted = re.sub(r'^\s*\.\s*', '', formatted)
        formatted = formatted.strip()
        
        if aggressive:
            # Remove weak language
            weak_words = ["might", "perhaps", "maybe", "possibly", "could", "should consider"]
            for word in weak_words:
                formatted = re.sub(rf"\b{word}\b", "", formatted, flags=re.IGNORECASE)
            
            # Make sentences more direct
            formatted = formatted.replace("You can ", "")
            formatted = formatted.replace("You should ", "")
            formatted = formatted.replace("You need to ", "")
            formatted = formatted.replace("It would be ", "It's ")
            formatted = formatted.replace("There is a ", "")
            formatted = formatted.replace("There are ", "")
        
        # Clean up any double spaces or punctuation
        formatted = re.sub(r'\s+', ' ', formatted)
        formatted = re.sub(r'\s+([.,!?])', r'\1', formatted)
        
        return formatted
    
    @classmethod
    def format_for_ticket(cls, title: str, description: str) -> Dict[str, str]:
        """
        Format ticket content in Clubhouse style.
        
        Args:
            title: Original ticket title
            description: Original ticket description
            
        Returns:
            Dict with formatted title and description
        """
        # Make title direct and descriptive
        formatted_title = cls.format_response(title, aggressive=True)
        formatted_title = formatted_title.upper() if len(formatted_title) < 50 else formatted_title
        
        # Format description as operational brief
        lines = description.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Add bullet if not already formatted
                if not line.startswith(('•', '-', '*', '→')):
                    line = f"→ {line}"
                formatted_lines.append(cls.format_response(line, aggressive=False))
        
        formatted_description = '\n'.join(formatted_lines)
        
        return {
            "title": formatted_title,
            "description": formatted_description
        }
    
    @classmethod
    def format_recommendation(cls, recommendations: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Format recommendations in Clubhouse style.
        
        Args:
            recommendations: List of recommendation dicts with 'action' and 'reason'
            
        Returns:
            Formatted recommendations
        """
        formatted = []
        
        for rec in recommendations:
            action = cls.format_response(rec.get("action", ""), aggressive=True)
            reason = cls.format_response(rec.get("reason", ""), aggressive=True)
            
            # Make action imperative
            action_words = action.split()
            if action_words and action_words[0].lower() not in ["install", "remove", "check", "verify", "update", "replace"]:
                # Try to make it imperative
                if action_words[0].lower() in ["the", "a", "an"]:
                    action = ' '.join(action_words[1:])
            
            formatted.append({
                "action": action.capitalize(),
                "reason": reason,
                "priority": rec.get("priority", "medium")
            })
        
        return formatted
    
    @classmethod
    def create_operational_summary(cls, task: str, status: str, layers: List[str]) -> str:
        """
        Create a brief operational summary.
        
        Args:
            task: The original task
            status: Current status
            layers: Affected system layers
            
        Returns:
            One-line operational summary
        """
        task_short = task[:40] + "..." if len(task) > 40 else task
        layers_str = "/".join(layers[:3])  # Max 3 layers
        
        status_map = {
            "approved": "CLEAR",
            "rejected": "BLOCKED", 
            "review_required": "REVIEW",
            "completed": "DONE",
            "failed": "FAILED"
        }
        
        status_text = status_map.get(status, status.upper())
        
        return f"[{status_text}] {task_short} | {layers_str}"
