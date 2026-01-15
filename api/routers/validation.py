from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from api.db.session import get_db
from api.core.security import get_current_user_or_client
from api.models import ValidateContentRequest, ValidateContentResponse, ContentType
from api.services.content_generation_service import content_generation_service
from api.services.curriculum_service import curriculum_service

router = APIRouter(prefix="/api/v1/validation", tags=["Content Validation"])

@router.post("/validate-content", response_model=ValidateContentResponse)
async def validate_content(
    request: ValidateContentRequest,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate educational content against quality criteria.
    
    Performs comprehensive validation including curriculum alignment,
    pedagogical quality, content accuracy, age appropriateness,
    language quality, accessibility, safety, bias checks, and completeness.
    
    Returns validation status (passed/failed/needs_review), detailed
    issues with fix suggestions, and overall quality score.
    
    Authentication: JWT token OR API Key (with content:validate permission)
    """
    start_time = datetime.utcnow()
    
    try:
        # Get curriculum data if OAs are specified
        curriculum_data = None
        if request.linked_oas:
            curriculum_data = await curriculum_service.get_oas_by_ids(
                db, request.linked_oas, request.grade_level, request.subject
            )
        
        # Perform validation
        result = await content_generation_service.validate_content(
            request, curriculum_data
        )
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return ValidateContentResponse(
            success=True,
            result=result,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "model": "gemini-2.5-pro",
                "validation_level": request.validation_level,
                "content_type": request.content_type.value,
                "checks_performed": result.total_checks,
                "overall_score": result.overall_score,
                "status": result.status.value
            },
            error=None
        )
        
    except Exception as e:
        return ValidateContentResponse(
            success=False,
            result=None,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "error_time": datetime.utcnow().isoformat()
            },
            error=str(e)
        )


@router.post("/quick-check", response_model=ValidateContentResponse)
async def quick_check_content(
    content: str,
    content_type: ContentType,
    grade_level: str,
    subject: str,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Quick validation check for content (minimal validation level).
    
    A lighter version of validate_content that only checks for
    critical errors and safety issues. Faster but less thorough.
    
    Authentication: JWT token OR API Key
    """
    request = ValidateContentRequest(
        content_type=content_type,
        content=content,
        grade_level=grade_level,
        subject=subject,
        validation_level="minimal",
        include_recommendations=False,
        include_fix_suggestions=False,
        content_id=None,
        linked_oas=None,
        categories_to_check=None
    )
    
    return await validate_content(request, auth, db)