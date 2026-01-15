from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from api.db.session import get_db
from api.core.security import get_current_user_or_client
from api.models import TutorChatRequest, TutorChatResponse
from api.services.content_generation_service import content_generation_service
from api.services.curriculum_service import curriculum_service

router = APIRouter(prefix="/api/v1/tutor", tags=["AI Tutor"])

# Simple session storage (in production, use Redis)
_sessions: dict = {}

@router.post("/chat", response_model=TutorChatResponse)
async def tutor_chat(
    request: TutorChatRequest,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with the AI tutor.
    
    Provides personalized educational support through conversation.
    The tutor can explain concepts, guide practice, ask Socratic
    questions, provide encouragement, and help with review.
    
    Supports NEE adaptations and different learning styles.
    
    Authentication: JWT token OR API Key (with tutor:chat permission)
    """
    start_time = datetime.utcnow()
    
    # Manage session
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
    
    try:
        # Get curriculum context if OAs provided
        curriculum_data = None
        if request.context.linked_oas:
            curriculum_data = await curriculum_service.get_oas_by_ids(
                db, 
                request.context.linked_oas,
                request.context.student_grade_level,
                request.context.subject
            )
        
        # Generate tutor response
        tutor_response = await content_generation_service.tutor_chat(
            request, curriculum_data
        )
        
        end_time = datetime.utcnow()
        
        # Track session topics (simplified)
        topics = _sessions.get(session_id, {}).get('topics', [])
        if request.context.current_topic and request.context.current_topic not in topics:
            topics.append(request.context.current_topic)
        _sessions[session_id] = {'topics': topics, 'last_active': datetime.utcnow()}
        
        return TutorChatResponse(
            success=True,
            response=tutor_response,
            session_id=session_id,
            topics_covered=topics,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_ms": int((end_time - start_time).total_seconds() * 1000),
                "model": "gemini-2.5-pro",
                "tutor_role": request.tutor_role.value,
                "response_style": request.response_style
            },
            error=None
        )
        
    except Exception as e:
        return TutorChatResponse(
            success=False,
            response=None,
            session_id=session_id,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "error_time": datetime.utcnow().isoformat()
            },
            error=str(e)
        )

@router.get("/sessions/{session_id}")
async def get_session_info(
    session_id: str,
    auth = Depends(get_current_user_or_client)
):
    """
    Get information about a tutoring session.
    
    Returns topics covered and session activity.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "topics_covered": session.get('topics', []),
        "last_active": session.get('last_active'),
        "is_active": True
    }

@router.delete("/sessions/{session_id}")
async def end_session(
    session_id: str,
    auth = Depends(get_current_user_or_client)
):
    """
    End a tutoring session.
    
    Clears session data.
    """
    if session_id in _sessions:
        del _sessions[session_id]
        return {"message": "Session ended", "session_id": session_id}
    
    raise HTTPException(status_code=404, detail="Session not found")