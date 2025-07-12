# backend/core/validator.py
from typing import Dict, Any, Optional
from backend.schemas import ClubCoreLLMResponse
import logging

logger = logging.getLogger(__name__)

class ResponseValidator:
    @staticmethod
    def validate_llm_response(response: Optional[Dict[str, Any]]) -> Optional[ClubCoreLLMResponse]:
        if not response:
            return None
            
        try:
            # Ensure required fields exist
            if not all(key in response for key in ["layers", "recommendation", "status", "confidence"]):
                logger.error("LLM response missing required fields")
                return None
            
            # Validate layers structure
            if not isinstance(response.get("layers"), list):
                logger.error("LLM response 'layers' is not a list")
                return None
                
            # Validate recommendation structure
            if not isinstance(response.get("recommendation"), list):
                logger.error("LLM response 'recommendation' is not a list")
                return None
            
            # Validate confidence
            confidence = response.get("confidence")
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                logger.error(f"Invalid confidence value: {confidence}")
                return None
            
            # Validate status
            valid_statuses = ["approved", "rejected", "review_required"]
            if response.get("status") not in valid_statuses:
                logger.error(f"Invalid status: {response.get('status')}")
                return None
            
            # Create and return validated response
            return ClubCoreLLMResponse(**response)
            
        except Exception as e:
            logger.error(f"Failed to validate LLM response: {e}")
            return None
