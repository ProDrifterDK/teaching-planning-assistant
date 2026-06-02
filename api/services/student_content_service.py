from api.core.config import settings
from api.models.student_content import (
    PathwayGenerationRequest,
    PathwayGenerationResponse,
    GeneratedPathway,
    GenerationMetadata,
    QuizGenerationRequest,
    QuizGenerationResponse,
    InteractiveQuiz,
    MisconceptionAnalysisRequest,
    MisconceptionAnalysisResponse,
    AdaptiveRecommendationResponse,
    ContentRecommendation,
    StudentInsights,
    RecommendationMetadata,
    RecommendationReason,
    LearningStats,
    StudentNEEType,
)
from api.prompts.student_content_prompts import (
    PATHWAY_GENERATION_PROMPT,
    QUIZ_GENERATION_PROMPT,
    MISCONCEPTION_ANALYSIS_PROMPT,
    ADAPTIVE_RECOMMENDATION_PROMPT,
)
from api.services.schema_utils import clean_schema_for_llm
from api.services.ai_adapter import DeepSeekAIAdapter, ai_adapter
import json
import uuid
import time
from typing import Optional, List, Dict, Any
from datetime import datetime


class StudentContentService:

    def __init__(self, adapter: Optional[DeepSeekAIAdapter] = None):
        self.adapter = adapter or ai_adapter

    async def _generate_json(self, prompt: str, response_model) -> tuple[dict, Any]:
        result = await self.adapter.generate_json(
            prompt,
            schema=clean_schema_for_llm(response_model.model_json_schema()),
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        )
        return result.data, result.usage

    async def generate_pathway(
        self, request: PathwayGenerationRequest, curriculum_data: dict
    ) -> PathwayGenerationResponse:
        start_time = time.time()

        try:
            oa_descriptions = "\n".join(
                [
                    f"- {oa['codigo']}: {oa['descripcion']}"
                    for oa in curriculum_data.get("oas", [])
                ]
            )

            class_profile_text = ""
            if request.class_profile:
                nee_list = ", ".join([n.value for n in request.class_profile.nee_profiles])
                class_profile_text = f"""
## Perfil de Clase
- Nivel promedio: {request.class_profile.average_level}
- NEE presentes: {nee_list if nee_list else "Ninguna"}
- Tamaño de clase: {request.class_profile.class_size} estudiantes
"""

            differentiation_text = ""
            if request.include_differentiation:
                differentiation_text = """
Incluir para cada nodo:
- differentiation_options.basic: Versión simplificada
- differentiation_options.intermediate: Versión estándar
- differentiation_options.advanced: Extensión/profundización
"""

            prompt = PATHWAY_GENERATION_PROMPT.format(
                subject=request.subject,
                grade_level=request.grade_level,
                unit_name=request.unit_name,
                oa_descriptions=oa_descriptions,
                mission_theme=request.mission_theme.value,
                hook_style=request.hook_style,
                estimated_total_minutes=request.estimated_total_minutes,
                chapters_count=request.chapters_count,
                include_checkpoints=request.include_checkpoints,
                include_side_quests=request.include_side_quests,
                class_profile_text=class_profile_text,
                differentiation_text=differentiation_text,
            )

            pathway_data, usage = await self._generate_json(prompt, GeneratedPathway)
            pathway = GeneratedPathway(**pathway_data)

            end_time = time.time()
            generation_time_ms = int((end_time - start_time) * 1000)

            metadata = GenerationMetadata(
                model=settings.AI_MODEL,
                tokens_input=usage.prompt_tokens,
                tokens_output=usage.completion_tokens,
                tokens_thinking=usage.reasoning_tokens,
                generation_time_ms=generation_time_ms,
                prompt_version="pathway_v1.0",
            )

            return PathwayGenerationResponse(
                success=True, pathway=pathway, metadata=metadata
            )

        except Exception as e:
            end_time = time.time()
            return PathwayGenerationResponse(
                success=False,
                pathway=None,
                metadata=GenerationMetadata(
                    generation_time_ms=int((end_time - start_time) * 1000)
                ),
                error=str(e),
            )

    async def generate_interactive_quiz(
        self, request: QuizGenerationRequest, curriculum_data: dict
    ) -> QuizGenerationResponse:
        start_time = time.time()

        try:
            oa_descriptions = "\n".join(
                [
                    f"- {oa['codigo']}: {oa['descripcion']}"
                    for oa in curriculum_data.get("oas", [])
                ]
            )

            topic_text = f"Tema: {request.topic}" if request.topic else ""
            time_limit_text = (
                f"{request.time_limit} minutos"
                if request.time_limit
                else "Sin límite"
            )
            time_limit_value = request.time_limit if request.time_limit else "null"

            question_types_distribution = ""
            for qt_config in request.question_types:
                question_types_distribution += f"- {qt_config.type.value}: {qt_config.count} preguntas\n"

            difficulty_distribution = "Distribución balanceada (30% fácil, 50% medio, 20% difícil)"
            if request.difficulty_distribution:
                difficulty_distribution = f"Easy: {request.difficulty_distribution.easy * 100}%, Medium: {request.difficulty_distribution.medium * 100}%, Hard: {request.difficulty_distribution.hard * 100}%"

            nee_adaptations_text = ""
            if request.generate_nee_adaptations and request.nee_types:
                nee_list = ", ".join([n.value for n in request.nee_types])
                nee_adaptations_text = f"""
## Adaptaciones NEE Requeridas
Generar adaptaciones para: {nee_list}
- TDAH: Más tiempo, pausas visuales, preguntas más cortas
- Dislexia: Fuente más grande, lectura en voz alta, lenguaje simplificado
- TEA: Estructura predecible, instrucciones claras, carga sensorial reducida
"""

            prompt = QUIZ_GENERATION_PROMPT.format(
                subject=request.subject or curriculum_data.get("subject", ""),
                curso=request.curso,
                quiz_type=request.quiz_type.value,
                topic_text=topic_text,
                oa_descriptions=oa_descriptions,
                num_questions=request.num_questions,
                time_limit_text=time_limit_text,
                time_limit_value=time_limit_value,
                difficulty_distribution=difficulty_distribution,
                feedback_level=request.feedback_level,
                question_types_distribution=question_types_distribution,
                nee_adaptations_text=nee_adaptations_text,
            )

            quiz_data, usage = await self._generate_json(prompt, InteractiveQuiz)

            if "id" not in quiz_data or not quiz_data["id"]:
                quiz_data["id"] = f"quiz_{uuid.uuid4().hex[:8]}"

            quiz_data = self._validate_and_fix_interactive_quiz(quiz_data, request)

            quiz = InteractiveQuiz(**quiz_data)

            end_time = time.time()
            generation_time_ms = int((end_time - start_time) * 1000)

            metadata = GenerationMetadata(
                model=settings.AI_MODEL,
                tokens_input=usage.prompt_tokens,
                tokens_output=usage.completion_tokens,
                tokens_thinking=usage.reasoning_tokens,
                generation_time_ms=generation_time_ms,
                prompt_version="quiz_v1.0",
            )

            return QuizGenerationResponse(success=True, quiz=quiz, metadata=metadata)

        except Exception as e:
            end_time = time.time()
            return QuizGenerationResponse(
                success=False,
                quiz=None,
                metadata=GenerationMetadata(
                    generation_time_ms=int((end_time - start_time) * 1000)
                ),
                error=str(e),
            )

    def _validate_and_fix_interactive_quiz(
        self, quiz_data: dict, request: QuizGenerationRequest
    ) -> dict:
        questions = quiz_data.get("questions", [])
        seen_ids = set()
        total_points = 0

        for i, q in enumerate(questions):
            if not q.get("id") or q.get("id") in seen_ids:
                q["id"] = f"q_{i + 1:03d}"
            seen_ids.add(q["id"])

            if "order" not in q:
                q["order"] = i + 1

            q_type = q.get("type", "multiple_choice")
            if q_type == "multiple_choice" and not q.get("options"):
                q["options"] = [
                    {"id": "a", "text": "Opción A", "is_correct": True},
                    {"id": "b", "text": "Opción B", "is_correct": False},
                    {"id": "c", "text": "Opción C", "is_correct": False},
                    {"id": "d", "text": "Opción D", "is_correct": False},
                ]
                q["correct_answer"] = {"type": "exact", "value": "a"}

            if "correct_answer" not in q or q["correct_answer"] is None:
                if q_type in ["multiple_choice", "true_false"]:
                    options = q.get("options", [])
                    correct_option = next(
                        (o for o in options if o.get("is_correct")), None
                    )
                    if correct_option:
                        q["correct_answer"] = {
                            "type": "exact",
                            "value": correct_option.get("id", "a"),
                        }
                    else:
                        q["correct_answer"] = {"type": "exact", "value": "a"}
                else:
                    q["correct_answer"] = {"type": "exact", "value": ""}

            if "feedback" not in q:
                q["feedback"] = {
                    "correct": "¡Correcto!",
                    "incorrect": "Incorrecto. Revisa tu respuesta.",
                }

            if "accessibility" not in q:
                q["accessibility"] = {}

            points = q.get("points", 10)
            total_points += points

        quiz_data["questions"] = questions
        quiz_data["total_points"] = total_points

        if "passing_score" not in quiz_data:
            quiz_data["passing_score"] = int(total_points * 0.7)

        if "instructions" not in quiz_data:
            quiz_data["instructions"] = (
                "Responde las siguientes preguntas. Lee cada pregunta cuidadosamente antes de responder."
            )

        if request.include_confidence_tracking and "confidence_instructions" not in quiz_data:
            quiz_data["confidence_instructions"] = (
                "Después de cada respuesta, indica qué tan seguro estás: "
                "Adivino, Algo seguro, Seguro, o Muy seguro."
            )

        return quiz_data

    async def get_adaptive_recommendations(
        self,
        student_id: str,
        current_pathway_id: Optional[str] = None,
        context_type: str = "continue",
        limit: int = 10,
        student_progress: Optional[Dict[str, Any]] = None,
        available_content: Optional[List[Dict[str, Any]]] = None,
    ) -> AdaptiveRecommendationResponse:
        recommendations = []

        if student_progress is None:
            student_progress = self._get_mock_student_progress(student_id)

        if available_content is None:
            available_content = self._get_mock_available_content()

        priority_weights = {
            "overdue_assignment": 100,
            "spaced_repetition_due": 80,
            "pathway_continuation": 70,
            "upcoming_assignment": 60,
            "adaptive_weak_area": 50,
            "interest_match": 40,
            "exploration": 30,
        }

        for content in available_content[:limit]:
            reason = self._determine_recommendation_reason(
                content, student_progress, current_pathway_id, context_type
            )

            priority = priority_weights.get(reason.value.replace("_next", "_continuation"), 50)

            if content.get("is_overdue"):
                priority += min(content.get("days_overdue", 0) * 10, 30)

            if content.get("has_misconception"):
                priority += 25

            recommendation = ContentRecommendation(
                content_id=content.get("id", f"content_{uuid.uuid4().hex[:8]}"),
                content_type=content.get("type", "lesson"),
                title=content.get("title", "Contenido"),
                description=content.get("description", ""),
                reason=reason,
                reason_explanation=self._get_reason_explanation(reason, content),
                priority=min(priority, 100),
                is_review=content.get("is_review", False),
                estimated_minutes=content.get("estimated_minutes", 15),
                difficulty=content.get("difficulty", "medium"),
                oa_code=content.get("oa_code"),
                skill=content.get("skill"),
                pathway_id=content.get("pathway_id"),
                pathway_title=content.get("pathway_title"),
                node_id=content.get("node_id"),
                chapter_title=content.get("chapter_title"),
                urgency=self._calculate_urgency(content, priority),
            )
            recommendations.append(recommendation)

        recommendations.sort(key=lambda x: x.priority, reverse=True)
        recommendations = recommendations[:limit]

        insights = StudentInsights(
            current_mastery_level=student_progress.get("mastery_level", "developing"),
            mastery_score=student_progress.get("mastery_score", 65.0),
            recent_trend=student_progress.get("trend", "stable"),
            suggested_focus_areas=[],
            alerts=[],
            learning_stats=LearningStats(
                total_time_this_week=student_progress.get("time_this_week", 0),
                content_completed_this_week=student_progress.get("completed_this_week", 0),
                average_score_this_week=student_progress.get("avg_score_this_week", 0.0),
                streak_days=student_progress.get("streak_days", 0),
            ),
        )

        metadata = RecommendationMetadata(
            generated_at=datetime.utcnow(),
            algorithm_version="adaptive_v1.0",
            factors_considered=[
                "pathway_progress",
                "spaced_repetition",
                "mastery_levels",
                "recent_activity",
            ],
        )

        return AdaptiveRecommendationResponse(
            recommendations=recommendations, insights=insights, metadata=metadata
        )

    def _determine_recommendation_reason(
        self,
        content: Dict[str, Any],
        student_progress: Dict[str, Any],
        current_pathway_id: Optional[str],
        context_type: str,
    ) -> RecommendationReason:
        if content.get("is_overdue"):
            return RecommendationReason.OVERDUE_ASSIGNMENT

        if content.get("review_due"):
            return RecommendationReason.REVIEW_DUE

        if (
            current_pathway_id
            and content.get("pathway_id") == current_pathway_id
            and content.get("is_next_in_pathway")
        ):
            return RecommendationReason.PATHWAY_NEXT

        if content.get("is_upcoming_assignment"):
            return RecommendationReason.UPCOMING_ASSIGNMENT

        if content.get("addresses_weak_area"):
            return RecommendationReason.WEAK_AREA

        if content.get("is_remedial"):
            return RecommendationReason.REMEDIAL_NEEDED

        if content.get("matches_interest"):
            return RecommendationReason.INTEREST_MATCH

        if content.get("is_prerequisite"):
            return RecommendationReason.PREREQUISITE

        return RecommendationReason.REINFORCEMENT

    def _get_reason_explanation(
        self, reason: RecommendationReason, content: Dict[str, Any]
    ) -> str:
        explanations = {
            RecommendationReason.PATHWAY_NEXT: f"Siguiente lección en tu misión '{content.get('pathway_title', '')}'",
            RecommendationReason.REVIEW_DUE: "Este contenido está programado para repaso según tu calendario de repetición espaciada",
            RecommendationReason.OVERDUE_ASSIGNMENT: "Tienes una tarea pendiente que debes completar",
            RecommendationReason.UPCOMING_ASSIGNMENT: "Prepárate para una evaluación próxima",
            RecommendationReason.WEAK_AREA: "Este tema necesita refuerzo según tu desempeño reciente",
            RecommendationReason.REMEDIAL_NEEDED: "Contenido de remediación para fortalecer conceptos base",
            RecommendationReason.INTEREST_MATCH: "Contenido relacionado con tus intereses",
            RecommendationReason.PREREQUISITE: "Concepto necesario antes de avanzar",
            RecommendationReason.REINFORCEMENT: "Práctica adicional para consolidar tu aprendizaje",
        }
        return explanations.get(reason, "Recomendado para tu progreso")

    def _calculate_urgency(
        self, content: Dict[str, Any], priority: int
    ) -> str:
        if priority >= 90 or content.get("is_overdue"):
            return "critical"
        elif priority >= 70:
            return "high"
        elif priority >= 50:
            return "normal"
        return "low"

    def _get_mock_student_progress(self, student_id: str) -> Dict[str, Any]:
        return {
            "mastery_level": "developing",
            "mastery_score": 68.5,
            "trend": "improving",
            "time_this_week": 45,
            "completed_this_week": 3,
            "avg_score_this_week": 75.0,
            "streak_days": 4,
        }

    def _get_mock_available_content(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "content_001",
                "type": "lesson",
                "title": "Comparando Fracciones",
                "description": "Aprende a comparar fracciones con diferentes denominadores",
                "estimated_minutes": 15,
                "difficulty": "medium",
                "oa_code": "MA05 OA 07",
                "skill": "Comparación de fracciones",
                "pathway_id": "pathway_001",
                "pathway_title": "Descubriendo las Fracciones",
                "is_next_in_pathway": True,
            },
            {
                "id": "content_002",
                "type": "review",
                "title": "Repaso: Partes de una Fracción",
                "description": "Repasa los conceptos de numerador y denominador",
                "estimated_minutes": 5,
                "difficulty": "easy",
                "oa_code": "MA05 OA 06",
                "skill": "Identificación de fracciones",
                "review_due": True,
                "is_review": True,
            },
        ]

    async def analyze_misconceptions(
        self, request: MisconceptionAnalysisRequest
    ) -> MisconceptionAnalysisResponse:
        start_time = time.time()

        try:
            wrong_answers_json = json.dumps(
                [wa.model_dump() for wa in request.wrong_answers], indent=2, default=str
            )

            nee_profile_text = ""
            if request.student_nee_profile:
                nee_profile_text = f"""
NEE del estudiante: {request.student_nee_profile.primary_nee.value if request.student_nee_profile.primary_nee else 'Ninguna'}
Acomodaciones: {', '.join(request.student_nee_profile.accommodations) if request.student_nee_profile.accommodations else 'Ninguna'}
"""

            special_considerations = ""
            if request.include_historical_context:
                special_considerations = "Considera patrones históricos de errores del estudiante si están disponibles."

            prompt = MISCONCEPTION_ANALYSIS_PROMPT.format(
                student_id=request.student_id,
                grade_level=request.grade_level,
                subject=request.subject,
                topic=request.topic,
                nee_profile_text=nee_profile_text,
                wrong_answers_json=wrong_answers_json,
                quiz_id=request.quiz_id,
                special_considerations=special_considerations,
                language="español" if request.language == "es" else "inglés",
            )

            analysis_data, usage = await self._generate_json(prompt, MisconceptionAnalysisResponse)

            analysis_data["quiz_id"] = request.quiz_id
            analysis_data["student_id"] = request.student_id
            analysis_data["analysis_timestamp"] = datetime.utcnow().isoformat()
            analysis_data["total_wrong_answers"] = len(request.wrong_answers)

            end_time = time.time()
            analysis_data["metadata"] = {
                "analysis_time_ms": int((end_time - start_time) * 1000),
                "model_version": settings.AI_MODEL,
                "tokens_input": usage.prompt_tokens,
                "tokens_output": usage.completion_tokens,
                "tokens_thinking": usage.reasoning_tokens,
                "historical_data_used": request.include_historical_context,
            }

            return MisconceptionAnalysisResponse(**analysis_data)

        except Exception as e:
            end_time = time.time()
            return MisconceptionAnalysisResponse(
                quiz_id=request.quiz_id,
                student_id=request.student_id,
                total_wrong_answers=len(request.wrong_answers),
                overall_understanding_score=0.0,
                metadata={
                    "error": str(e),
                    "analysis_time_ms": int((end_time - start_time) * 1000),
                },
            )


student_content_service = StudentContentService()
