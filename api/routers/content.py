from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from api.db.session import get_db
from api.core.security import get_current_user_or_client
from api.models import (
    GenerateQuizRequest, GenerateQuizResponse,
    AdaptContentRequest, AdaptContentResponse,
    GenerateActivityRequest, GenerateActivityResponse,
    GenerateExamRequest, GenerateExamResponse,
    GenerateReinforcementRequest, GenerateReinforcementResponse,
    GenerateSummaryRequest, GenerateSummaryResponse
)
from api.services.content_generation_service import content_generation_service
from api.services.curriculum_service import curriculum_service

router = APIRouter(prefix="/api/v1/content", tags=["Content Generation"])

@router.post("/adapt-content", response_model=AdaptContentResponse)
async def adapt_content(
    request: AdaptContentRequest,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Adapt educational content for students with Special Educational Needs (NEE).
    
    Takes original content and adapts it based on student's NEE profile,
    applying evidence-based strategies for each identified need. Returns
    adapted content with teacher guidance and implementation checklist.
    
    Supported NEE types include: dyslexia, dyscalculia, ADHD, autism spectrum,
    visual/hearing impairments, intellectual disabilities, and giftedness.
    
    Authentication: JWT token OR API Key (with content:adapt permission)
    """
    start_time = datetime.utcnow()
    
    try:
        # Generate the adapted content
        adapted_content = await content_generation_service.adapt_content_for_nee(request)
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return AdaptContentResponse(
            success=True,
            adapted_content=adapted_content,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "model": "gemini-2.5-pro",
                "nee_types": [nee.value for nee in request.nee_types],
                "adaptation_level": request.adaptation_level.value,
                "content_type": request.content_type.value
            },
            error=None
        )
        
    except Exception as e:
        return AdaptContentResponse(
            success=False,
            adapted_content=None,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "error_time": datetime.utcnow().isoformat()
            },
            error=str(e)
        )

@router.post("/generate-quiz", response_model=GenerateQuizResponse)
async def generate_quiz(
    request: GenerateQuizRequest,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a quiz based on curriculum OAs or a topic.
    
    Creates a structured quiz with various question types suitable for
    formative or summative assessment. Questions are aligned to specific
    OAs (if available) or generated based on topic and curriculum context.
    
    Authentication: JWT token OR API Key (with content:generate permission)
    """
    start_time = datetime.utcnow()
    
    try:
        curriculum_data = {'oas': []}
        generation_mode = "topic_based"
        
        # Try to get curriculum data if OA IDs are provided
        if request.oa_ids:
            curriculum_data = await curriculum_service.get_oas_by_ids(
                db, request.oa_ids, request.grade_level, request.subject
            )
            if curriculum_data.get('oas'):
                generation_mode = "oa_based"
        
        # If no OAs found but topic provided, generate topic-based content
        if not curriculum_data.get('oas'):
            if request.topic:
                # Create synthetic curriculum data from topic
                curriculum_data = {
                    'oas': [{
                        'codigo': f'TOPIC_{request.topic[:20].upper().replace(" ", "_")}',
                        'descripcion': f'Contenido basado en el tema: {request.topic}',
                        'eje': request.subject,
                        'habilidades': ['Comprender', 'Aplicar', 'Analizar'],
                        'actitudes': []
                    }],
                    'topic': request.topic,
                    'is_topic_based': True
                }
                generation_mode = "topic_based"
            else:
                return GenerateQuizResponse(
                    success=False,
                    quiz=None,
                    generation_metadata={
                        "requested_at": start_time.isoformat(),
                        "duration_ms": 0
                    },
                    error="No valid OAs found and no topic provided. Please provide either valid OA IDs or a topic."
                )
        
        # Generate the quiz
        quiz = await content_generation_service.generate_quiz(
            request, curriculum_data
        )
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return GenerateQuizResponse(
            success=True,
            quiz=quiz,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "model": "gemini-2.5-pro",
                "generation_mode": generation_mode,
                "oas_used": request.oa_ids if generation_mode == "oa_based" else [],
                "topic": request.topic if generation_mode == "topic_based" else None,
                "num_questions": len(quiz.questions)
            },
            error=None
        )
        
    except Exception as e:
        return GenerateQuizResponse(
            success=False,
            quiz=None,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "error_time": datetime.utcnow().isoformat()
            },
            error=str(e)
        )

@router.post("/generate-activity", response_model=GenerateActivityResponse)
async def generate_activity(
    request: GenerateActivityRequest,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate interactive learning activities based on curriculum OAs.
    
    Creates structured activities with steps, resources, timing,
    and differentiation options. Supports various activity types
    including group work, hands-on, games, and projects.
    """
    start_time = datetime.utcnow()
    
    try:
        # Get curriculum data
        curriculum_data = await curriculum_service.get_oas_by_ids(
            db, request.oa_ids, request.grade_level, request.subject
        )
        
        if not curriculum_data.get('oas'):
            return GenerateActivityResponse(
                success=False,
                activity=None,
                generation_metadata={
                    "requested_at": start_time.isoformat(),
                    "duration_ms": 0
                },
                error="No valid OAs found for the given identifiers"
            )
            
        # Generate activity
        activity = await content_generation_service.generate_activity(
            request, curriculum_data
        )
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return GenerateActivityResponse(
            success=True,
            activity=activity,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "model": "gemini-2.5-pro",
                "oas_used": request.oa_ids,
                "activity_type": request.activity_type.value if request.activity_type else "auto"
            },
            error=None
        )
        
    except Exception as e:
        return GenerateActivityResponse(
            success=False,
            activity=None,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "error_time": datetime.utcnow().isoformat()
            },
            error=str(e)
        )

@router.post("/generate-exam", response_model=GenerateExamResponse)
async def generate_exam(
    request: GenerateExamRequest,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate summative exams with multiple sections.
    
    Creates comprehensive exams with balanced coverage of OAs,
    various question types, and optional answer keys and rubrics.
    """
    start_time = datetime.utcnow()
    
    try:
        # Get curriculum data
        curriculum_data = await curriculum_service.get_oas_by_ids(
            db, request.oa_ids, request.grade_level, request.subject
        )
        
        if not curriculum_data.get('oas'):
            return GenerateExamResponse(
                success=False,
                exam=None,
                generation_metadata={
                    "requested_at": start_time.isoformat(),
                    "duration_ms": 0
                },
                error="No valid OAs found for the given identifiers"
            )
            
        # Generate exam
        exam = await content_generation_service.generate_exam(
            request, curriculum_data
        )
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return GenerateExamResponse(
            success=True,
            exam=exam,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "model": "gemini-2.5-pro",
                "oas_used": request.oa_ids,
                "total_points": exam.total_points
            },
            error=None
        )
        
    except Exception as e:
        return GenerateExamResponse(
            success=False,
            exam=None,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "error_time": datetime.utcnow().isoformat()
            },
            error=str(e)
        )

@router.post("/generate-reinforcement", response_model=GenerateReinforcementResponse)
async def generate_reinforcement(
    request: GenerateReinforcementRequest,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate reinforcement materials for struggling students.
    
    Creates a personalized reinforcement plan with various materials
    like concept reviews, practice exercises, visual guides, and
    worked examples. Includes guidance for teachers and parents.
    """
    start_time = datetime.utcnow()
    
    try:
        # Get curriculum data
        curriculum_data = await curriculum_service.get_oas_by_ids(
            db, request.oa_ids, request.grade_level, request.subject
        )
        
        if not curriculum_data.get('oas'):
            return GenerateReinforcementResponse(
                success=False,
                reinforcement_plan=None,
                generation_metadata={
                    "requested_at": start_time.isoformat(),
                    "duration_ms": 0
                },
                error="No valid OAs found for the given identifiers"
            )
            
        # Generate reinforcement plan
        plan = await content_generation_service.generate_reinforcement(
            request, curriculum_data
        )
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return GenerateReinforcementResponse(
            success=True,
            reinforcement_plan=plan,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "model": "gemini-2.5-pro",
                "oas_used": request.oa_ids,
                "num_materials": len(plan.materials)
            },
            error=None
        )
        
    except Exception as e:
        return GenerateReinforcementResponse(
            success=False,
            reinforcement_plan=None,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "error_time": datetime.utcnow().isoformat()
            },
            error=str(e)
        )

@router.post("/generate-summary", response_model=GenerateSummaryResponse)
async def generate_summary(
    request: GenerateSummaryRequest,
    auth = Depends(get_current_user_or_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a unit summary for student study and review.
    
    Creates comprehensive summaries in various formats including
    bullet points, concept maps, and flashcard sets. Includes
    study questions, common misconceptions, and self-assessment.
    """
    start_time = datetime.utcnow()
    
    try:
        curriculum_data = await curriculum_service.get_oas_by_ids(
            db, request.oa_ids, request.grade_level, request.subject
        )
        
        if not curriculum_data.get('oas'):
            return GenerateSummaryResponse(
                success=False,
                summary=None,
                generation_metadata={"requested_at": start_time.isoformat()},
                error="No valid OAs found"
            )
        
        summary = await content_generation_service.generate_summary(
            request, curriculum_data
        )
        
        end_time = datetime.utcnow()
        
        return GenerateSummaryResponse(
            success=True,
            summary=summary,
            generation_metadata={
                "requested_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_ms": int((end_time - start_time).total_seconds() * 1000),
                "format": request.format.value
            },
            error=None
        )
        
    except Exception as e:
        return GenerateSummaryResponse(
            success=False,
            summary=None,
            generation_metadata={"requested_at": start_time.isoformat()},
            error=str(e)
        )