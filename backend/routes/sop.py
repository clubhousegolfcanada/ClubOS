# backend/routes/sop.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from backend.core.enhanced_sop_resolver import EnhancedSOPResolver
from backend.schemas import ClubCoreLLMResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class SOPResolveRequest(BaseModel):
    issue_description: str
    context: Optional[Dict[str, Any]] = {}
    auto_execute: bool = True

# Initialize resolver
sop_resolver = EnhancedSOPResolver()

@router.post("/sop/resolve", response_model=ClubCoreLLMResponse)
async def resolve_with_sop(request: SOPResolveRequest):
    """
    Resolve an operational issue using SOPs from Google Drive.
    Uses cached SOPs with optional auto-execution.
    """
    try:
        logger.info(f"SOP resolution requested for: {request.issue_description}")
        
        result = await sop_resolver.resolve(
            issue_description=request.issue_description,
            context=request.context,
            auto_execute=request.auto_execute
        )
        
        return result
        
    except Exception as e:
        logger.error(f"SOP resolution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sop/sync-status")
async def get_sync_status():
    """
    Get Google Drive sync status.
    """
    return sop_resolver.get_sync_status()

@router.post("/sop/refresh")
async def refresh_sops():
    """
    Manually refresh SOPs from Google Drive.
    """
    try:
        result = sop_resolver.refresh_sops()
        return result
    except Exception as e:
        logger.error(f"SOP refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
