from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
from enum import Enum


class InteractiveQuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    MULTIPLE_SELECT = "multiple_select"
    TRUE_FALSE = "true_false"
    MATCHING = "matching"
    ORDERING = "ordering"
    FILL_IN_BLANK = "fill_in_blank"
    SHORT_ANSWER = "short_answer"
    DRAG_DROP = "drag_drop"
    IMAGE_HOTSPOT = "image_hotspot"


class ConfidenceLevel(str, Enum):
    GUESS = "guess"
    SOMEWHAT_SURE = "somewhat_sure"
    CONFIDENT = "confident"
    CERTAIN = "certain"


class MissionTheme(str, Enum):
    ADVENTURE = "adventure"
    MYSTERY = "mystery"
    BUILDING = "building"
    DISCOVERY = "discovery"
    QUEST = "quest"


class StudentNEEType(str, Enum):
    TDAH = "tdah"
    DISLEXIA = "dislexia"
    TEA = "tea"
    DISCAPACIDAD_VISUAL = "discapacidad_visual"
    DISCAPACIDAD_AUDITIVA = "discapacidad_auditiva"
    DISCALCULIA = "discalculia"
    MOTORA = "motora"
    INTELECTUAL = "intelectual"
    SUPERDOTACION = "superdotacion"


class RecommendationReason(str, Enum):
    PATHWAY_NEXT = "pathway_next"
    REVIEW_DUE = "review_due"
    OVERDUE_ASSIGNMENT = "overdue_assignment"
    UPCOMING_ASSIGNMENT = "upcoming_assignment"
    WEAK_AREA = "weak_area"
    REMEDIAL_NEEDED = "remedial_needed"
    INTEREST_MATCH = "interest_match"
    PREREQUISITE = "prerequisite"
    REINFORCEMENT = "reinforcement"


class QuizTypeLiteral(str, Enum):
    FORMATIVE = "formative"
    DIAGNOSTIC = "diagnostic"
    SUMMATIVE = "summative"
    REVIEW = "review"
    CHECKPOINT = "checkpoint"


class DifficultyLiteral(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADAPTIVE = "adaptive"


class ClassProfileRequest(BaseModel):
    average_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    nee_profiles: List[StudentNEEType] = Field(default_factory=list)
    class_size: int = Field(default=30, ge=1, le=50)


class MissionMetaphor(BaseModel):
    name: str = Field(..., description="Mission narrative name, e.g., 'El Explorador de Fracciones'")
    icon: str = Field(..., description="Emoji icon for the mission")
    narrative: str = Field(..., description="Story context for the mission")
    theme: MissionTheme


class NodeCompletionConfig(BaseModel):
    default_next_node_id: Optional[str] = None
    conditional_next: List[Dict[str, Any]] = Field(default_factory=list)


class NodeFailureConfig(BaseModel):
    remedial_content_prompt: Optional[str] = None
    retry_allowed: bool = True
    max_retries: int = 2


class DifferentiationOptions(BaseModel):
    basic: Optional[str] = None
    intermediate: Optional[str] = None
    advanced: Optional[str] = None


class PathwayNode(BaseModel):
    id: str
    order: int = Field(..., ge=1)
    type: Literal["hook", "lesson", "activity", "quiz", "assessment", "checkpoint"]
    title: str
    description: str
    content_generation_prompt: str = Field(..., description="Instructions for content generation")
    objectives: List[str]
    estimated_minutes: int = Field(..., ge=1)
    is_required: bool = True
    is_checkpoint: bool = False
    on_complete: NodeCompletionConfig
    on_fail: Optional[NodeFailureConfig] = None
    differentiation_options: Optional[DifferentiationOptions] = None


class ChapterCompletionCriteria(BaseModel):
    required_node_ids: List[str]
    minimum_score: int = Field(default=60, ge=0, le=100)


class CheckpointQuizConfig(BaseModel):
    num_questions: int = Field(default=5, ge=1, le=20)
    question_types: List[InteractiveQuestionType] = Field(default_factory=list)
    passing_score: int = Field(default=70, ge=0, le=100)


class SideQuestDefinition(BaseModel):
    title: str
    description: str
    content_generation_prompt: str
    available_after_node_order: int
    bonus_xp: int = Field(default=50, ge=0)
    estimated_minutes: int = Field(default=10, ge=1)


class PathwayChapter(BaseModel):
    id: str
    order: int = Field(..., ge=1)
    title: str
    description: str
    nodes: List[PathwayNode]
    completion_criteria: ChapterCompletionCriteria
    checkpoint_quiz: Optional[CheckpointQuizConfig] = None
    side_quests: List[SideQuestDefinition] = Field(default_factory=list)


class PathwayRewards(BaseModel):
    xp_on_complete: int = Field(default=500, ge=0)
    suggested_badge_id: Optional[str] = None
    certificate_eligible: bool = True


class SuggestedPrerequisites(BaseModel):
    oa_codes: List[str] = Field(default_factory=list)
    pathway_ids: Optional[List[str]] = None
    minimum_mastery: int = Field(default=70, ge=0, le=100)


class GeneratedPathway(BaseModel):
    title: str
    description: str
    mission_metaphor: MissionMetaphor
    chapters: List[PathwayChapter]
    total_nodes: int
    total_checkpoints: int
    estimated_total_minutes: int
    rewards: PathwayRewards
    suggested_prerequisites: SuggestedPrerequisites


class GenerationMetadata(BaseModel):
    model: str = "gemini-2.5-pro"
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_thinking: int = 0
    generation_time_ms: int = 0
    cost_usd: float = 0.0
    prompt_version: str = "v1.0"


class PathwayGenerationRequest(BaseModel):
    grade_level: int = Field(..., ge=1, le=12, description="Grade level (1-8 for básico, 9-12 for medio)")
    subject: str = Field(..., description="Subject name (e.g., 'Matemáticas', 'Lenguaje')")
    oa_codes: List[str] = Field(..., min_length=1, max_length=10, description="OA codes to cover")
    unit_name: str = Field(..., max_length=100, description="Unit name (e.g., 'Fracciones')")
    estimated_total_minutes: int = Field(default=180, ge=30, le=600)
    chapters_count: int = Field(default=3, ge=2, le=5)
    include_checkpoints: bool = True
    include_side_quests: bool = True
    mission_theme: MissionTheme = MissionTheme.DISCOVERY
    hook_style: Literal["question", "story", "problem", "video"] = "problem"
    class_profile: Optional[ClassProfileRequest] = None
    include_multiple_formats: bool = True
    include_differentiation: bool = True


class PathwayGenerationResponse(BaseModel):
    success: bool
    pathway: Optional[GeneratedPathway] = None
    metadata: GenerationMetadata
    error: Optional[str] = None


class QuestionTypeConfig(BaseModel):
    type: InteractiveQuestionType
    count: int = Field(default=1, ge=0, le=10)
    weight: Optional[float] = Field(default=None, ge=0.5, le=3.0)


class DifficultyDistribution(BaseModel):
    easy: float = Field(default=0.3, ge=0, le=1)
    medium: float = Field(default=0.5, ge=0, le=1)
    hard: float = Field(default=0.2, ge=0, le=1)

    @field_validator("hard")
    @classmethod
    def validate_total(cls, v, info):
        easy = info.data.get("easy", 0)
        medium = info.data.get("medium", 0)
        total = easy + medium + v
        if abs(total - 1.0) > 0.01:
            raise ValueError("Difficulty distribution must sum to 1.0")
        return v


class UDLOptions(BaseModel):
    include_visual_support: bool = True
    include_audio_descriptions: bool = True
    include_simplified_versions: bool = True
    include_hints: bool = True
    hint_levels: int = Field(default=2, ge=1, le=3)


class QuizGenerationRequest(BaseModel):
    content_id: Optional[str] = Field(None, description="Generate for specific content")
    oa_codes: Optional[List[str]] = Field(None, description="Generate for OA codes")
    curso: str = Field(..., description="Course identifier")
    quiz_type: QuizTypeLiteral = QuizTypeLiteral.FORMATIVE
    num_questions: int = Field(default=10, ge=3, le=20)
    time_limit: Optional[int] = Field(None, ge=1, le=120, description="Time limit in minutes")
    question_types: List[QuestionTypeConfig] = Field(
        default_factory=lambda: [
            QuestionTypeConfig(type=InteractiveQuestionType.MULTIPLE_CHOICE, count=4),
            QuestionTypeConfig(type=InteractiveQuestionType.TRUE_FALSE, count=2),
            QuestionTypeConfig(type=InteractiveQuestionType.FILL_IN_BLANK, count=2),
            QuestionTypeConfig(type=InteractiveQuestionType.MATCHING, count=2),
        ]
    )
    difficulty: DifficultyLiteral = DifficultyLiteral.MEDIUM
    difficulty_distribution: Optional[DifficultyDistribution] = None
    include_confidence_tracking: bool = True
    udl_options: UDLOptions = Field(default_factory=UDLOptions)
    generate_nee_adaptations: bool = True
    nee_types: Optional[List[StudentNEEType]] = None
    for_spaced_repetition: bool = False
    student_id: Optional[str] = None
    review_item_ids: Optional[List[str]] = None
    feedback_level: Literal["none", "correct_incorrect", "with_explanation", "detailed"] = "with_explanation"
    subject: Optional[str] = None
    topic: Optional[str] = None
    context: Optional[str] = None


class QuestionMedia(BaseModel):
    type: Literal["image", "audio", "video"]
    url: str
    alt_text: Optional[str] = None


class QuestionOption(BaseModel):
    id: str
    text: str
    is_correct: bool
    feedback: Optional[str] = None


class MatchingPairItem(BaseModel):
    left_id: str
    left_text: str
    right_id: str
    right_text: str


class OrderingItemDef(BaseModel):
    id: str
    text: str


class BlankDefinition(BaseModel):
    id: str
    correct_answers: List[str]
    position: int


class DraggableItem(BaseModel):
    id: str
    label: str


class DropZone(BaseModel):
    id: str
    label: str
    correct_item_ids: List[str]


class DragDropConfigModel(BaseModel):
    items: List[DraggableItem]
    zones: List[DropZone]
    allow_multiple_in_zone: bool = False
    click_to_select_enabled: bool = True
    allow_reorder: bool = True


class AnswerSpec(BaseModel):
    type: Literal["exact", "contains", "regex", "numeric_range"]
    value: Any


class ConfidencePoints(BaseModel):
    correct: float
    incorrect: float


class ConfidenceScoring(BaseModel):
    guess: ConfidencePoints = Field(default_factory=lambda: ConfidencePoints(correct=0, incorrect=0))
    somewhat_sure: ConfidencePoints = Field(default_factory=lambda: ConfidencePoints(correct=1, incorrect=-0.5))
    confident: ConfidencePoints = Field(default_factory=lambda: ConfidencePoints(correct=2, incorrect=-1))
    certain: ConfidencePoints = Field(default_factory=lambda: ConfidencePoints(correct=3, incorrect=-2))


class QuestionFeedback(BaseModel):
    correct: str
    incorrect: str
    partial: Optional[str] = None
    option_feedback: Optional[Dict[str, str]] = None
    explanation_media: Optional[QuestionMedia] = None
    misconception_addressed: Optional[str] = None


class QuestionHint(BaseModel):
    level: int = Field(..., ge=1, le=3)
    text: str
    point_deduction: int = Field(default=0, ge=0)


class SimplifiedQuestion(BaseModel):
    stem: str
    options: Optional[List[QuestionOption]] = None


class QuestionAccessibility(BaseModel):
    read_aloud_text: Optional[str] = None
    simplified_version: Optional[SimplifiedQuestion] = None
    visual_support: Optional[str] = None
    audio_description: Optional[str] = None
    extended_time_recommended: bool = False
    keyboard_navigation_enabled: bool = True


class InteractiveQuestion(BaseModel):
    id: str
    type: InteractiveQuestionType
    order: int
    stem: str
    media: List[QuestionMedia] = Field(default_factory=list)
    options: Optional[List[QuestionOption]] = None
    matching_pairs: Optional[List[MatchingPairItem]] = None
    ordering_items: Optional[List[OrderingItemDef]] = None
    blanks: Optional[List[BlankDefinition]] = None
    drag_drop_config: Optional[DragDropConfigModel] = None
    correct_answer: AnswerSpec
    points: int = Field(default=10, ge=1)
    partial_credit_allowed: bool = False
    difficulty: Literal["easy", "medium", "hard"]
    skill: str
    oa_code: Optional[str] = None
    confidence_enabled: bool = True
    confidence_scoring: Optional[ConfidenceScoring] = None
    feedback: QuestionFeedback
    hints: List[QuestionHint] = Field(default_factory=list)
    accessibility: QuestionAccessibility = Field(default_factory=QuestionAccessibility)
    concept_id: Optional[str] = None
    importance_level: Optional[Literal["critical", "important", "supplementary"]] = None


class NEEQuizAdaptation(BaseModel):
    time_multiplier: float = Field(default=1.0, ge=1.0, le=3.0)
    visual_breaks: bool = False
    reduced_question_count: Optional[int] = None
    gamification_enhanced: bool = False
    font_size_increase: float = Field(default=1.0, ge=1.0, le=2.0)
    text_to_speech_enabled: bool = False
    simplified_language: bool = False
    extended_time: bool = False
    predictable_structure: bool = False
    reduced_sensory_load: bool = False
    clear_instructions: bool = False
    progress_visibility: Literal["always", "on_request", "hidden"] = "always"


class InteractiveQuiz(BaseModel):
    id: str
    title: str
    type: str
    oa_codes: List[str]
    time_limit: Optional[int] = None
    total_points: int
    passing_score: int
    instructions: str
    confidence_instructions: Optional[str] = None
    questions: List[InteractiveQuestion]
    nee_adaptations: Optional[Dict[str, NEEQuizAdaptation]] = None


class QuizGenerationResponse(BaseModel):
    success: bool
    quiz: Optional[InteractiveQuiz] = None
    metadata: GenerationMetadata
    error: Optional[str] = None


class SpacedRepetitionContext(BaseModel):
    last_reviewed_at: Optional[datetime] = None
    current_interval: int = 1
    current_ease_factor: float = 2.5
    repetition_count: int = 0


class ContentRecommendation(BaseModel):
    content_id: str
    content_type: Literal["lesson", "quiz", "activity", "review", "remedial"]
    title: str
    description: str
    reason: RecommendationReason
    reason_explanation: str
    priority: int = Field(default=50, ge=0, le=100)
    is_review: bool = False
    estimated_minutes: int
    difficulty: Literal["easy", "medium", "hard"]
    oa_code: Optional[str] = None
    skill: Optional[str] = None
    pathway_id: Optional[str] = None
    pathway_title: Optional[str] = None
    node_id: Optional[str] = None
    chapter_title: Optional[str] = None
    urgency: Literal["low", "normal", "high", "critical"] = "normal"
    due_date: Optional[datetime] = None
    overdue_by: Optional[int] = None
    spaced_repetition: Optional[SpacedRepetitionContext] = None


class FocusArea(BaseModel):
    oa_code: str
    skill: str
    current_mastery: float = Field(ge=0, le=100)
    suggested_action: str
    priority: Literal["low", "medium", "high"]


class StudentAlert(BaseModel):
    type: Literal["misconception", "declining_performance", "inactivity", "struggling", "excellence"]
    message: str
    urgency: Literal["low", "medium", "high"]
    related_content_ids: List[str] = Field(default_factory=list)
    suggested_action: Optional[str] = None


class LearningStats(BaseModel):
    total_time_this_week: int = 0
    content_completed_this_week: int = 0
    average_score_this_week: float = 0.0
    streak_days: int = 0


class StudentInsights(BaseModel):
    current_mastery_level: Literal["beginning", "emerging", "developing", "proficient", "mastered"]
    mastery_score: float = Field(ge=0, le=100)
    recent_trend: Literal["improving", "stable", "declining"]
    suggested_focus_areas: List[FocusArea] = Field(default_factory=list)
    alerts: List[StudentAlert] = Field(default_factory=list)
    learning_stats: LearningStats = Field(default_factory=LearningStats)


class RecommendationMetadata(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    algorithm_version: str = "adaptive_v1.0"
    factors_considered: List[str] = Field(default_factory=list)


class AdaptiveRecommendationResponse(BaseModel):
    recommendations: List[ContentRecommendation] = Field(default_factory=list)
    insights: StudentInsights
    metadata: RecommendationMetadata


class WrongAnswer(BaseModel):
    question_id: str
    question_type: InteractiveQuestionType
    question_stem: str
    correct_answer: Any
    student_answer: Any
    time_spent_seconds: int = Field(ge=0)
    confidence_level: Optional[ConfidenceLevel] = None
    hint_used: bool = False
    attempt_number: int = Field(default=1, ge=1)


class NEEProfile(BaseModel):
    primary_nee: Optional[StudentNEEType] = None
    secondary_nee: Optional[List[StudentNEEType]] = None
    accommodations: List[str] = Field(default_factory=list)


class MisconceptionAnalysisRequest(BaseModel):
    student_id: str = Field(..., min_length=1, description="Student identifier")
    quiz_id: str = Field(..., min_length=1, description="Quiz identifier")
    subject: str = Field(..., description="Subject area (e.g., 'Matemáticas')")
    grade_level: int = Field(..., ge=1, le=12)
    topic: str = Field(..., description="Specific topic (e.g., 'Fracciones')")
    wrong_answers: List[WrongAnswer] = Field(..., min_length=1)
    student_nee_profile: Optional[NEEProfile] = None
    include_historical_context: bool = True
    language: str = Field(default="es", pattern="^(es|en)$")


class DetectedMisconception(BaseModel):
    id: str
    name: str
    description: str
    affected_question_ids: List[str] = Field(..., min_length=1)
    confidence_score: float = Field(ge=0, le=1)
    severity: Literal["low", "medium", "high", "critical"]
    is_persistent: bool = False
    category: str


class RemediationSuggestion(BaseModel):
    misconception_id: str
    suggestion_type: Literal[
        "review_content",
        "practice_quiz",
        "video_explanation",
        "hands_on_activity",
        "peer_tutoring",
        "teacher_intervention",
    ]
    title: str
    description: str
    estimated_time_minutes: int
    priority: Literal["immediate", "soon", "when_available"]
    content_reference: Optional[str] = None
    generated_content: Optional[Dict[str, Any]] = None


class TeacherAlert(BaseModel):
    alert_level: Literal["info", "warning", "urgent"]
    student_id: str
    student_name: Optional[str] = None
    summary: str
    detailed_analysis: str
    recommended_actions: List[str]
    related_misconceptions: List[str]
    requires_acknowledgment: bool = False


class MisconceptionAnalysisResponse(BaseModel):
    quiz_id: str
    student_id: str
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_wrong_answers: int
    misconceptions_detected: List[DetectedMisconception] = Field(default_factory=list)
    remediation_suggestions: List[RemediationSuggestion] = Field(default_factory=list)
    teacher_alert: Optional[TeacherAlert] = None
    overall_understanding_score: float = Field(ge=0, le=1)
    knowledge_gaps: List[str] = Field(default_factory=list)
    strengths_identified: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
