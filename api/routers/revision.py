from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from api.db.session import get_db
from api.core.security import get_current_user_or_client
from api.models import ContentRevisionRequest, ContentRevisionResponse
from api.services.revision_service import revision_service

router = APIRouter(prefix="/api/v1/content", tags=["Content Revision"])

@router.post("/revise", response_model=ContentRevisionResponse)
async def revise_content(
    request: ContentRevisionRequest,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Revise educational content based on teacher feedback.
    
    Takes original content (quiz, lesson, etc.) and applies requested changes
    such as simplifying vocabulary, adding examples, or shortening content.
    
    Authentication: JWT token OR API Key (with content:generate permission)
    """
    start_time = datetime.utcnow()
    
    try:
        # Perform revision
        response = await revision_service.revise_content(request)
        return response
        
    except Exception as e:
        return ContentRevisionResponse(
            success=False,
            revised_content=None,
            changes_summary=None,
            revision_metadata={
                "requested_at": start_time.isoformat(),
                "error_time": datetime.utcnow().isoformat()
            },
            error=str(e)
        )
