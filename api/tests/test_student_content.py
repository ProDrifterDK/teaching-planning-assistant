import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from api.models.student_content import (
    PathwayGenerationRequest,
    PathwayGenerationResponse,
    QuizGenerationRequest,
    QuizGenerationResponse,
    MisconceptionAnalysisRequest,
    MisconceptionAnalysisResponse,
    AdaptiveRecommendationResponse,
    MissionTheme,
    QuizTypeLiteral,
    InteractiveQuestionType,
    QuestionTypeConfig,
    WrongAnswer,
    ConfidenceLevel,
    GenerationMetadata,
)
from api.services.student_content_service import StudentContentService


@pytest.fixture
def student_content_service():
    with patch("api.services.student_content_service.genai") as mock_genai:
        mock_genai.configure = MagicMock()
        mock_genai.GenerativeModel = MagicMock()
        service = StudentContentService()
        yield service


@pytest.fixture
def sample_curriculum_data():
    return {
        "oas": [
            {
                "codigo": "MA05 OA 06",
                "descripcion": "Resolver problemas con fracciones",
                "eje": "Números y Operaciones",
                "habilidades": ["Resolver", "Analizar"],
                "actitudes": [],
            },
            {
                "codigo": "MA05 OA 07",
                "descripcion": "Comparar fracciones",
                "eje": "Números y Operaciones",
                "habilidades": ["Comparar", "Ordenar"],
                "actitudes": [],
            },
        ],
        "subject": "Matemáticas",
    }


class TestPathwayGeneration:
    def test_pathway_request_validation(self):
        request = PathwayGenerationRequest(
            grade_level=5,
            subject="Matemáticas",
            oa_codes=["MA05 OA 06", "MA05 OA 07"],
            unit_name="Fracciones",
            estimated_total_minutes=180,
            chapters_count=3,
            mission_theme=MissionTheme.DISCOVERY,
        )
        
        assert request.grade_level == 5
        assert request.subject == "Matemáticas"
        assert len(request.oa_codes) == 2
        assert request.mission_theme == MissionTheme.DISCOVERY

    def test_pathway_request_with_class_profile(self):
        from api.models.student_content import ClassProfileRequest, StudentNEEType
        
        class_profile = ClassProfileRequest(
            average_level="intermediate",
            nee_profiles=[StudentNEEType.TDAH, StudentNEEType.DISLEXIA],
            class_size=28,
        )
        
        request = PathwayGenerationRequest(
            grade_level=5,
            subject="Matemáticas",
            oa_codes=["MA05 OA 06"],
            unit_name="Fracciones",
            class_profile=class_profile,
        )
        
        assert request.class_profile is not None
        assert len(request.class_profile.nee_profiles) == 2

    def test_pathway_request_invalid_grade(self):
        with pytest.raises(ValueError):
            PathwayGenerationRequest(
                grade_level=15,
                subject="Matemáticas",
                oa_codes=["MA05 OA 06"],
                unit_name="Fracciones",
            )

    def test_pathway_request_empty_oa_codes(self):
        with pytest.raises(ValueError):
            PathwayGenerationRequest(
                grade_level=5,
                subject="Matemáticas",
                oa_codes=[],
                unit_name="Fracciones",
            )


class TestQuizGeneration:
    def test_quiz_request_validation(self):
        request = QuizGenerationRequest(
            curso="5° Básico",
            oa_codes=["MA05 OA 06"],
            quiz_type=QuizTypeLiteral.FORMATIVE,
            num_questions=10,
            question_types=[
                QuestionTypeConfig(type=InteractiveQuestionType.MULTIPLE_CHOICE, count=4),
                QuestionTypeConfig(type=InteractiveQuestionType.TRUE_FALSE, count=2),
                QuestionTypeConfig(type=InteractiveQuestionType.FILL_IN_BLANK, count=2),
                QuestionTypeConfig(type=InteractiveQuestionType.MATCHING, count=2),
            ],
        )
        
        assert request.num_questions == 10
        assert len(request.question_types) == 4
        assert request.quiz_type == QuizTypeLiteral.FORMATIVE

    def test_quiz_request_with_confidence_tracking(self):
        request = QuizGenerationRequest(
            curso="5° Básico",
            oa_codes=["MA05 OA 06"],
            include_confidence_tracking=True,
        )
        
        assert request.include_confidence_tracking is True

    def test_quiz_request_with_nee_adaptations(self):
        from api.models.student_content import StudentNEEType
        
        request = QuizGenerationRequest(
            curso="5° Básico",
            oa_codes=["MA05 OA 06"],
            generate_nee_adaptations=True,
            nee_types=[StudentNEEType.TDAH, StudentNEEType.DISLEXIA],
        )
        
        assert request.generate_nee_adaptations is True
        assert len(request.nee_types) == 2

    def test_quiz_request_for_spaced_repetition(self):
        request = QuizGenerationRequest(
            curso="5° Básico",
            oa_codes=["MA05 OA 06"],
            for_spaced_repetition=True,
            student_id="student_123",
            review_item_ids=["item_1", "item_2", "item_3"],
        )
        
        assert request.for_spaced_repetition is True
        assert request.student_id == "student_123"

    def test_question_type_distribution(self):
        request = QuizGenerationRequest(
            curso="5° Básico",
            oa_codes=["MA05 OA 06"],
            question_types=[
                QuestionTypeConfig(type=InteractiveQuestionType.MULTIPLE_CHOICE, count=5),
                QuestionTypeConfig(type=InteractiveQuestionType.DRAG_DROP, count=3),
                QuestionTypeConfig(type=InteractiveQuestionType.ORDERING, count=2),
            ],
        )
        
        total_questions = sum(qt.count for qt in request.question_types)
        assert total_questions == 10


class TestMisconceptionAnalysis:
    def test_misconception_request_validation(self):
        wrong_answers = [
            WrongAnswer(
                question_id="q_001",
                question_type=InteractiveQuestionType.MULTIPLE_CHOICE,
                question_stem="¿Qué fracción es equivalente a 1/2?",
                correct_answer="2/4",
                student_answer="1/4",
                time_spent_seconds=45,
                confidence_level=ConfidenceLevel.CONFIDENT,
                hint_used=False,
                attempt_number=1,
            )
        ]
        
        request = MisconceptionAnalysisRequest(
            student_id="student_123",
            quiz_id="quiz_001",
            subject="Matemáticas",
            grade_level=5,
            topic="Fracciones equivalentes",
            wrong_answers=wrong_answers,
        )
        
        assert request.student_id == "student_123"
        assert len(request.wrong_answers) == 1
        assert request.wrong_answers[0].confidence_level == ConfidenceLevel.CONFIDENT

    def test_misconception_request_with_nee_profile(self):
        from api.models.student_content import NEEProfile, StudentNEEType
        
        nee_profile = NEEProfile(
            primary_nee=StudentNEEType.DISLEXIA,
            accommodations=["extended_time", "text_to_speech"],
        )
        
        wrong_answers = [
            WrongAnswer(
                question_id="q_001",
                question_type=InteractiveQuestionType.MULTIPLE_CHOICE,
                question_stem="Test question",
                correct_answer="a",
                student_answer="b",
                time_spent_seconds=30,
            )
        ]
        
        request = MisconceptionAnalysisRequest(
            student_id="student_123",
            quiz_id="quiz_001",
            subject="Matemáticas",
            grade_level=5,
            topic="Fracciones",
            wrong_answers=wrong_answers,
            student_nee_profile=nee_profile,
        )
        
        assert request.student_nee_profile.primary_nee == StudentNEEType.DISLEXIA


class TestAdaptiveRecommendations:
    @pytest.mark.asyncio
    async def test_adaptive_recommendations_basic(self, student_content_service):
        response = await student_content_service.get_adaptive_recommendations(
            student_id="student_123",
            context_type="continue",
            limit=5,
        )
        
        assert isinstance(response, AdaptiveRecommendationResponse)
        assert response.insights is not None
        assert response.metadata is not None

    @pytest.mark.asyncio
    async def test_adaptive_recommendations_with_pathway(self, student_content_service):
        response = await student_content_service.get_adaptive_recommendations(
            student_id="student_123",
            current_pathway_id="pathway_001",
            context_type="continue",
            limit=10,
        )
        
        assert isinstance(response, AdaptiveRecommendationResponse)

    @pytest.mark.asyncio
    async def test_adaptive_recommendations_review_mode(self, student_content_service):
        response = await student_content_service.get_adaptive_recommendations(
            student_id="student_123",
            context_type="review",
            limit=5,
        )
        
        assert isinstance(response, AdaptiveRecommendationResponse)


class TestServiceIntegration:
    @pytest.mark.asyncio
    async def test_generate_pathway_mocked(self, student_content_service, sample_curriculum_data):
        mock_response = MagicMock()
        mock_response.text = """{
            "title": "Descubriendo las Fracciones",
            "description": "Una aventura matemática",
            "mission_metaphor": {
                "name": "El Explorador",
                "icon": "🗺️",
                "narrative": "Embárcate en una aventura",
                "theme": "discovery"
            },
            "chapters": [],
            "total_nodes": 0,
            "total_checkpoints": 0,
            "estimated_total_minutes": 180,
            "rewards": {
                "xp_on_complete": 500,
                "certificate_eligible": true
            },
            "suggested_prerequisites": {
                "oa_codes": [],
                "minimum_mastery": 70
            }
        }"""
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 200
        
        student_content_service.model.generate_content_async = AsyncMock(return_value=mock_response)
        
        request = PathwayGenerationRequest(
            grade_level=5,
            subject="Matemáticas",
            oa_codes=["MA05 OA 06"],
            unit_name="Fracciones",
        )
        
        response = await student_content_service.generate_pathway(request, sample_curriculum_data)
        
        assert response.success is True
        assert response.pathway is not None
        assert response.pathway.title == "Descubriendo las Fracciones"

    @pytest.mark.asyncio
    async def test_generate_quiz_mocked(self, student_content_service, sample_curriculum_data):
        mock_response = MagicMock()
        mock_response.text = """{
            "id": "quiz_001",
            "title": "Quiz de Fracciones",
            "type": "formative",
            "oa_codes": ["MA05 OA 06"],
            "total_points": 100,
            "passing_score": 70,
            "instructions": "Responde las preguntas",
            "questions": [
                {
                    "id": "q_001",
                    "type": "multiple_choice",
                    "order": 1,
                    "stem": "¿Cuál es el numerador de 3/4?",
                    "options": [
                        {"id": "a", "text": "3", "is_correct": true},
                        {"id": "b", "text": "4", "is_correct": false}
                    ],
                    "correct_answer": {"type": "exact", "value": "a"},
                    "points": 10,
                    "difficulty": "easy",
                    "skill": "Identificación",
                    "confidence_enabled": true,
                    "feedback": {
                        "correct": "¡Correcto!",
                        "incorrect": "Incorrecto"
                    },
                    "accessibility": {}
                }
            ]
        }"""
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 150
        mock_response.usage_metadata.candidates_token_count = 300
        
        student_content_service.model.generate_content_async = AsyncMock(return_value=mock_response)
        
        request = QuizGenerationRequest(
            curso="5° Básico",
            oa_codes=["MA05 OA 06"],
            subject="Matemáticas",
            num_questions=5,
        )
        
        response = await student_content_service.generate_interactive_quiz(request, sample_curriculum_data)
        
        assert response.success is True
        assert response.quiz is not None

    @pytest.mark.asyncio
    async def test_analyze_misconceptions_mocked(self, student_content_service):
        mock_response = MagicMock()
        mock_response.text = """{
            "quiz_id": "quiz_001",
            "student_id": "student_123",
            "total_wrong_answers": 1,
            "misconceptions_detected": [
                {
                    "id": "misc_001",
                    "name": "Confusión numerador-denominador",
                    "description": "El estudiante confunde la posición del numerador",
                    "affected_question_ids": ["q_001"],
                    "confidence_score": 0.85,
                    "severity": "medium",
                    "is_persistent": false,
                    "category": "conceptual_error"
                }
            ],
            "remediation_suggestions": [],
            "overall_understanding_score": 0.6,
            "knowledge_gaps": ["Identificación de numerador"],
            "strengths_identified": [],
            "next_steps": ["Revisar conceptos básicos"]
        }"""
        
        student_content_service.model.generate_content_async = AsyncMock(return_value=mock_response)
        
        wrong_answers = [
            WrongAnswer(
                question_id="q_001",
                question_type=InteractiveQuestionType.MULTIPLE_CHOICE,
                question_stem="¿Cuál es el numerador?",
                correct_answer="3",
                student_answer="4",
                time_spent_seconds=30,
            )
        ]
        
        request = MisconceptionAnalysisRequest(
            student_id="student_123",
            quiz_id="quiz_001",
            subject="Matemáticas",
            grade_level=5,
            topic="Fracciones",
            wrong_answers=wrong_answers,
        )
        
        response = await student_content_service.analyze_misconceptions(request)
        
        assert response.student_id == "student_123"
        assert response.total_wrong_answers == 1


class TestQuestionTypes:
    def test_all_question_types_defined(self):
        expected_types = [
            "multiple_choice",
            "multiple_select",
            "true_false",
            "matching",
            "ordering",
            "fill_in_blank",
            "short_answer",
            "drag_drop",
            "image_hotspot",
        ]
        
        actual_types = [t.value for t in InteractiveQuestionType]
        
        for expected in expected_types:
            assert expected in actual_types

    def test_drag_drop_config(self):
        from api.models.student_content import DragDropConfigModel, DraggableItem, DropZone
        
        config = DragDropConfigModel(
            items=[
                DraggableItem(id="item1", label="1/2"),
                DraggableItem(id="item2", label="3/4"),
            ],
            zones=[
                DropZone(id="zone1", label="Menor que 1/2", correct_item_ids=[]),
                DropZone(id="zone2", label="Mayor que 1/2", correct_item_ids=["item2"]),
            ],
            allow_multiple_in_zone=True,
            click_to_select_enabled=True,
        )
        
        assert len(config.items) == 2
        assert len(config.zones) == 2
        assert config.click_to_select_enabled is True


class TestConfidenceScoring:
    def test_confidence_scoring_defaults(self):
        from api.models.student_content import ConfidenceScoring
        
        scoring = ConfidenceScoring()
        
        assert scoring.guess.correct == 0
        assert scoring.guess.incorrect == 0
        assert scoring.certain.correct == 3
        assert scoring.certain.incorrect == -2

    def test_confidence_levels(self):
        levels = [l.value for l in ConfidenceLevel]
        
        assert "guess" in levels
        assert "somewhat_sure" in levels
        assert "confident" in levels
        assert "certain" in levels


class TestNEEAdaptations:
    def test_nee_quiz_adaptation(self):
        from api.models.student_content import NEEQuizAdaptation
        
        adaptation = NEEQuizAdaptation(
            time_multiplier=1.5,
            visual_breaks=True,
            reduced_question_count=5,
            gamification_enhanced=True,
            text_to_speech_enabled=True,
            simplified_language=True,
        )
        
        assert adaptation.time_multiplier == 1.5
        assert adaptation.visual_breaks is True
        assert adaptation.text_to_speech_enabled is True

    def test_all_nee_types_defined(self):
        from api.models.student_content import StudentNEEType
        
        expected_nee = [
            "tdah",
            "dislexia",
            "tea",
            "discapacidad_visual",
            "discapacidad_auditiva",
            "discalculia",
        ]
        
        actual_nee = [n.value for n in StudentNEEType]
        
        for expected in expected_nee:
            assert expected in actual_nee
