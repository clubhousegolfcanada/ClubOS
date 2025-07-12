# backend/core/llm.py
import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "sk-your-openai-key-here":
            logger.warning("OpenAI API key not configured - LLM features disabled")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
            
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "30"))
        
    async def get_completion(self, prompt: str, system_prompt: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            logger.warning("LLM client not initialized - using fallback")
            return None
            
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                ),
                timeout=self.timeout
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except asyncio.TimeoutError:
            logger.warning(f"LLM request timed out after {self.timeout} seconds")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return None

llm_service = LLMService()
