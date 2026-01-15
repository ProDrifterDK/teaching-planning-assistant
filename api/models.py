from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from enum import Enum

class Attitude(BaseModel):
    codigo: str
    descripcion: str

class OA(BaseModel):
    oa_codigo_oficial: str
    descripcion_oa: str
    desglose_componentes: List[str] = Field(default_factory=list)
    habilidades: List[str] = Field(default_factory=list)

class Eje(BaseModel):
    nombre_eje: str
    oas: List[OA]

class AsignaturaCurso(BaseModel):
    asignatura: str
    curso: str
    actitudes: List[Attitude]
    ejes: List[Eje]

class NivelDetail(BaseModel):
    curso: str
    asignaturas: List[str]

class AttachmentDetail(BaseModel):
    filename: str
    gemini_uri: str

class MultimodalResources(BaseModel):
    youtube_urls: Optional[List[str]] = Field(None)
    attachments: Optional[List[AttachmentDetail]] = Field(None)

class PlanRequest(BaseModel):
    oa_codigo_oficial: str = Field(..., description="Código oficial del OA a planificar.")
    curso: Optional[str] = Field(None, description="Curso seleccionado, para desambiguar OAs compartidos.")
    
    recurso_principal: str = Field(..., description="Recurso central sobre el cual girará la clase.")
    nivel_real_estudiantes: str = Field(..., description="Descripción cualitativa del nivel del curso.")
    
    materiales_disponibles: Optional[str] = Field(None, description="Recursos materiales con los que cuenta el docente en la sala.")
    duracion_clase_minutos: int = Field(90, description="Duración total de la sesión pedagógica en minutos.")
    
    numero_estudiantes: Optional[int] = Field(None, description="Número total de estudiantes en el aula.")
    diversidad_aula: Optional[str] = Field(None, description="Contexto sobre la diversidad, incluyendo necesidades especiales (NEE/PIE).")
    clima_de_aula: Optional[str] = Field(None, description="Dinámica y comportamiento general del grupo.")
    
    estilo_docente_preferido: Optional[str] = Field(None, description="Enfoque metodológico que el docente prefiere.")
    tipo_evaluacion_formativa: Optional[str] = Field(None, description="Instrumento o actividad de evaluación formativa específica.")
    
    contexto_unidad: Optional[str] = Field(None, description="Momento de la secuencia didáctica en que se enmarca la clase.")
    conocimientos_previos_requeridos: Optional[str] = Field(None, description="Habilidad o contenido prerrequisito que se necesite reforzar.")
    solicitud_especial: Optional[str] = Field(None, description="Instrucciones o notas adicionales del profesor para guiar la generación.")
    
    multimodal_resources: Optional[MultimodalResources] = Field(None, description="Recursos multimodales (videos, archivos) asociados a la planificación.")

    class Config:
        json_schema_extra = {
            "example": {
                "oa_codigo_oficial": "LE07 OA 03",
                "recurso_principal": "El cuento 'El gigante egoísta' de Oscar Wilde.",
                "nivel_real_estudiantes": "Nivel de 6° Básico en comprensión lectora.",
                "materiales_disponibles": "Pizarra, proyector, hojas blancas y lápices de colores.",
                "duracion_clase_minutos": 90,
                "numero_estudiantes": 38,
                "diversidad_aula": "Hay 2 estudiantes con TEA en el espectro 1, necesitan instrucciones claras.",
                "clima_de_aula": "Son creativos y les gusta dibujar, pero se distraen en actividades largas.",
                "estilo_docente_preferido": "Aprendizaje colaborativo en grupos",
                "tipo_evaluacion_formativa": "Crear un mini-cómic de 3 viñetas",
                "contexto_unidad": "Es la clase de cierre de la Unidad 1: 'El héroe en distintas épocas'.",
                "conocimientos_previos_requeridos": "Diferenciar entre acciones de personajes y sus motivaciones.",
                "multimodal_resources": {
                    "youtube_urls": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
                    "attachments": [
                        {"filename": "diagrama_heroe.png", "gemini_uri": "files/abcdef123456"}
                    ]
                }
            }
        }

class PlanResponse(BaseModel):
    planificacion: str

# --- Modelos para Planificación Estructurada ---

class BloomLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"

class LessonObjective(BaseModel):
    """A single learning objective"""
    objective_id: str = Field(..., description="Unique identifier for the objective")
    description: str = Field(..., description="The learning objective text")
    bloom_level: BloomLevel = Field(..., description="Bloom's taxonomy level")
    success_criteria: List[str] = Field(..., description="Measurable success criteria")

class LessonActivity(BaseModel):
    """A lesson activity with timing and resources"""
    activity_id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Activity title")
    description: str = Field(..., description="Detailed activity description")
    duration_minutes: int = Field(..., description="Duration in minutes")
    activity_type: str = Field(..., description="Type: introduction, development, closure, etc.")
    teacher_actions: List[str] = Field(..., description="What the teacher does")
    student_actions: List[str] = Field(..., description="What students do")
    materials: List[str] = Field(default=[], description="Required materials")
    differentiation_notes: Optional[str] = Field(None, description="Notes for differentiation")

class AssessmentCriteria(BaseModel):
    """Assessment criteria for evaluating learning"""
    criterion_id: str = Field(..., description="Unique identifier")
    description: str = Field(..., description="What is being assessed")
    levels: dict = Field(..., description="Performance levels (e.g., beginning, developing, proficient)")
    weight: float = Field(default=1.0, description="Weight in overall assessment")

class LessonSection(BaseModel):
    """A section of the lesson (e.g., Introduction, Development, Closure)"""
    section_type: str = Field(..., description="Section type")
    duration_minutes: int = Field(..., description="Total section duration")
    activities: List[LessonActivity] = Field(..., description="Activities in this section")

class StructuredLesson(BaseModel):
    """Complete structured lesson plan"""
    lesson_id: str = Field(..., description="Unique lesson identifier")
    title: str = Field(..., description="Lesson title")
    subject: str = Field(..., description="Subject area")
    grade_level: str = Field(..., description="Grade level (e.g., '5° Básico')")
    unit: str = Field(..., description="Curriculum unit")
    duration_minutes: int = Field(..., description="Total lesson duration")
    
    # Learning objectives linked to OAs
    objectives: List[LessonObjective] = Field(..., description="Learning objectives")
    linked_oas: List[str] = Field(..., description="Linked curriculum OA codes")
    
    # Lesson structure
    prerequisite_knowledge: List[str] = Field(..., description="Required prior knowledge")
    key_concepts: List[str] = Field(..., description="Key concepts covered")
    key_vocabulary: List[str] = Field(..., description="Key vocabulary terms")
    
    # Sections
    sections: List[LessonSection] = Field(..., description="Lesson sections")
    
    # Assessment
    assessment_criteria: List[AssessmentCriteria] = Field(..., description="Assessment rubric")
    formative_assessment: str = Field(..., description="How learning is checked during lesson")
    
    # Additional metadata
    cross_curricular_links: List[str] = Field(default=[], description="Links to other subjects")
    resources: List[str] = Field(default=[], description="External resources")
    teacher_notes: Optional[str] = Field(None, description="Additional notes for teacher")

class StructuredPlanRequest(BaseModel):
    """Request model for structured plan generation"""
    oa_ids: Optional[List[str]] = Field(default=None, description="List of OA identifiers to base lesson on (optional if topic provided)")
    topic: Optional[str] = Field(default=None, description="Topic for content generation (used when OA IDs not available)")
    grade_level: str = Field(..., description="Grade level (e.g., '5', '5° Básico')")
    subject: str = Field(..., description="Subject (e.g., 'Matemáticas', 'Lenguaje')")
    duration_minutes: int = Field(default=90, description="Desired lesson duration")
    context: Optional[str] = Field(None, description="Additional context or requirements")
    language: str = Field(default="es", description="Output language (es, en)")
    
    # Optional configuration
    include_differentiation: bool = Field(default=True, description="Include differentiation notes")
    include_assessment_rubric: bool = Field(default=True, description="Include assessment rubric")
    bloom_levels: Optional[List[BloomLevel]] = Field(None, description="Target Bloom's levels")

class StructuredPlanResponse(BaseModel):
    """Response model for structured plan generation"""
    success: bool = Field(..., description="Whether generation succeeded")
    lesson: Optional[StructuredLesson] = Field(None, description="The generated lesson")
    generation_metadata: dict = Field(..., description="Metadata about generation")
    error: Optional[str] = Field(None, description="Error message if failed")

# --- Modelos para Generación de Quizzes ---

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    ORDERING = "ordering"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class MultipleChoiceOption(BaseModel):
    """Option for multiple choice questions"""
    option_id: str = Field(..., description="Option identifier (a, b, c, d)")
    text: str = Field(..., description="Option text")
    is_correct: bool = Field(..., description="Whether this is the correct answer")
    feedback: Optional[str] = Field(None, description="Feedback if selected")

class MatchingPair(BaseModel):
    """Pair for matching questions"""
    left_id: str
    left_text: str
    right_id: str
    right_text: str

class QuizQuestion(BaseModel):
    """A single quiz question"""
    question_id: str = Field(..., description="Unique question identifier")
    question_type: QuestionType = Field(..., description="Type of question")
    question_text: str = Field(..., description="The question text")
    difficulty: DifficultyLevel = Field(..., description="Question difficulty")
    points: int = Field(default=1, description="Points for correct answer")
    linked_oa: str = Field(..., description="OA code this question assesses")
    bloom_level: BloomLevel = Field(..., description="Bloom's taxonomy level")
    
    # Type-specific fields (use appropriate one based on question_type)
    options: Optional[List[MultipleChoiceOption]] = Field(None, description="For multiple choice")
    correct_answer: Optional[str] = Field(None, description="For true/false, short answer, fill blank")
    matching_pairs: Optional[List[MatchingPair]] = Field(None, description="For matching")
    correct_order: Optional[List[str]] = Field(None, description="For ordering questions")
    
    # Feedback and hints
    explanation: str = Field(..., description="Explanation of correct answer")
    hint: Optional[str] = Field(None, description="Optional hint for students")

class Quiz(BaseModel):
    """Complete quiz structure"""
    quiz_id: str = Field(..., description="Unique quiz identifier")
    title: str = Field(..., description="Quiz title")
    description: str = Field(..., description="Quiz description/instructions")
    subject: str = Field(..., description="Subject area")
    grade_level: str = Field(..., description="Grade level")
    
    # Quiz configuration
    total_points: int = Field(..., description="Total possible points")
    time_limit_minutes: Optional[int] = Field(None, description="Time limit if any")
    passing_score_percent: int = Field(default=60, description="Passing score percentage")
    shuffle_questions: bool = Field(default=True, description="Whether to shuffle questions")
    show_feedback: bool = Field(default=True, description="Show feedback after submission")
    
    # Questions
    questions: List[QuizQuestion] = Field(..., description="Quiz questions")
    
    # Metadata
    linked_oas: List[str] = Field(..., description="All OAs covered")
    # Note: Using str for distributions because Gemini can't handle Dict[str, int]
    difficulty_distribution: str = Field(..., description="Count by difficulty as string, e.g. 'easy: 2, medium: 3, hard: 1'")
    bloom_distribution: str = Field(..., description="Count by Bloom level as string, e.g. 'remember: 1, apply: 2'")

class GenerateQuizRequest(BaseModel):
    """Request model for quiz generation"""
    oa_ids: Optional[List[str]] = Field(default=None, description="OA identifiers to base quiz on (optional if topic provided)")
    topic: Optional[str] = Field(default=None, description="Topic for quiz generation (used when OA IDs not available)")
    grade_level: str = Field(..., description="Grade level")
    subject: str = Field(..., description="Subject")
    
    # Quiz configuration
    num_questions: int = Field(default=10, ge=1, le=50, description="Number of questions")
    question_types: Optional[List[QuestionType]] = Field(
        None,
        description="Allowed question types (default: all)"
    )
    difficulty_distribution: Optional[dict] = Field(
        None,
        description="Distribution like {'easy': 3, 'medium': 5, 'hard': 2}"
    )
    bloom_levels: Optional[List[BloomLevel]] = Field(
        None,
        description="Target Bloom's levels"
    )
    time_limit_minutes: Optional[int] = Field(None, description="Time limit")
    
    # Content options
    context: Optional[str] = Field(None, description="Additional context")
    language: str = Field(default="es", description="Output language")
    include_hints: bool = Field(default=True, description="Include hints")
    include_explanations: bool = Field(default=True, description="Include explanations")

class GenerateQuizResponse(BaseModel):
    """Response model for quiz generation"""
    success: bool = Field(..., description="Whether generation succeeded")
    quiz: Optional[Quiz] = Field(None, description="The generated quiz")
    generation_metadata: dict = Field(..., description="Metadata about generation")
    error: Optional[str] = Field(None, description="Error message if failed")

# --- Modelos para Adaptación NEE ---

class NEEType(str, Enum):
    """Types of Special Educational Needs"""
    # Learning Disabilities
    DYSLEXIA = "dyslexia"
    DYSCALCULIA = "dyscalculia"
    DYSGRAPHIA = "dysgraphia"
    ADHD = "adhd"
    
    # Intellectual
    MILD_INTELLECTUAL = "mild_intellectual_disability"
    MODERATE_INTELLECTUAL = "moderate_intellectual_disability"
    
    # Sensory
    VISUAL_IMPAIRMENT = "visual_impairment"
    HEARING_IMPAIRMENT = "hearing_impairment"
    
    # Communication
    SPEECH_DISORDER = "speech_disorder"
    LANGUAGE_DISORDER = "language_disorder"
    
    # Autism Spectrum
    AUTISM_SPECTRUM = "autism_spectrum"
    ASPERGER = "asperger"
    
    # Physical
    MOTOR_DISABILITY = "motor_disability"
    
    # Emotional/Behavioral
    EMOTIONAL_DISORDER = "emotional_behavioral_disorder"
    
    # Giftedness (also requires adaptation)
    GIFTED = "gifted_talented"

class AdaptationLevel(str, Enum):
    """Level of adaptation required"""
    MINIMAL = "minimal"       # Small adjustments
    MODERATE = "moderate"     # Significant modifications
    EXTENSIVE = "extensive"   # Major restructuring

class ContentType(str, Enum):
    """Type of content being adapted"""
    LESSON = "lesson"
    QUIZ = "quiz"
    ACTIVITY = "activity"
    EXAM = "exam"
    READING = "reading"
    WORKSHEET = "worksheet"

class AdaptationStrategy(BaseModel):
    """A specific adaptation strategy applied"""
    strategy_id: str = Field(..., description="Unique identifier")
    strategy_name: str = Field(..., description="Name of the strategy")
    description: str = Field(..., description="What this strategy does")
    implementation: str = Field(..., description="How it was implemented")
    rationale: str = Field(..., description="Why this helps the student")

class VisualAdaptation(BaseModel):
    """Visual presentation adaptations"""
    font_size_increase: Optional[int] = Field(None, description="Percentage increase")
    font_family_recommendation: Optional[str] = Field(None, description="Recommended font")
    line_spacing: Optional[float] = Field(None, description="Line spacing multiplier")
    contrast_mode: Optional[str] = Field(None, description="high_contrast, dark_mode, etc.")
    image_descriptions: Optional[List[str]] = Field(None, description="Alt text for images")
    simplified_diagrams: bool = Field(default=False)

class CognitiveAdaptation(BaseModel):
    """Cognitive load adaptations"""
    simplified_vocabulary: bool = Field(default=False)
    shorter_sentences: bool = Field(default=False)
    chunked_content: bool = Field(default=False)
    additional_examples: int = Field(default=0, description="Number of extra examples added")
    visual_supports: List[str] = Field(default=[], description="Visual aids added")
    step_by_step_breakdown: bool = Field(default=False)
    memory_aids: List[str] = Field(default=[], description="Mnemonics, etc.")

class TemporalAdaptation(BaseModel):
    """Time and pacing adaptations"""
    extended_time_percent: int = Field(default=0, description="Extra time percentage")
    breaks_recommended: bool = Field(default=False)
    break_frequency_minutes: Optional[int] = Field(None)
    reduced_workload_percent: Optional[int] = Field(None)

class SupportAdaptation(BaseModel):
    """Support and scaffolding adaptations"""
    peer_support_recommended: bool = Field(default=False)
    adult_support_level: str = Field(default="minimal", description="minimal, moderate, intensive")
    assistive_technology: List[str] = Field(default=[], description="Recommended AT")
    manipulatives_needed: List[str] = Field(default=[])
    audio_support: bool = Field(default=False)

class AdaptedContent(BaseModel):
    """The adapted content with all modifications"""
    original_content_id: str = Field(..., description="Reference to original content")
    adapted_content_id: str = Field(..., description="ID of this adaptation")
    adaptation_profile: str = Field(..., description="Summary of NEE profile addressed")
    
    # The adapted content itself
    title: str = Field(..., description="Adapted title")
    content: str = Field(..., description="The adapted content (markdown)")
    content_html: Optional[str] = Field(None, description="HTML version if applicable")
    
    # Adaptation details
    strategies_applied: List[AdaptationStrategy] = Field(..., description="All strategies used")
    visual_adaptations: Optional[VisualAdaptation] = None
    cognitive_adaptations: Optional[CognitiveAdaptation] = None
    temporal_adaptations: Optional[TemporalAdaptation] = None
    support_adaptations: Optional[SupportAdaptation] = None
    
    # Teacher guidance
    teacher_notes: str = Field(..., description="Notes for implementing adaptations")
    implementation_checklist: List[str] = Field(..., description="Checklist for teacher")
    success_indicators: List[str] = Field(..., description="How to measure success")
    
    # Accessibility
    accessibility_score: float = Field(..., ge=0, le=100, description="Accessibility rating")
    wcag_compliance: List[str] = Field(default=[], description="WCAG guidelines addressed")

class AdaptContentRequest(BaseModel):
    """Request model for content adaptation"""
    # Content to adapt
    content_type: ContentType = Field(..., description="Type of content")
    original_content: str = Field(..., description="The original content to adapt (markdown or JSON string)")
    original_content_id: Optional[str] = Field(None, description="ID reference if from TPA")
    
    # Student profile
    nee_types: List[NEEType] = Field(..., description="Student's NEE types")
    adaptation_level: AdaptationLevel = Field(default=AdaptationLevel.MODERATE)
    student_grade_level: str = Field(..., description="Student's grade level")
    student_age: Optional[int] = Field(None, description="Student's age")
    
    # Additional context
    student_strengths: Optional[List[str]] = Field(None, description="Student's strengths")
    student_challenges: Optional[List[str]] = Field(None, description="Specific challenges")
    previous_successful_strategies: Optional[List[str]] = Field(None, description="What has worked before")
    
    # Adaptation preferences
    maintain_learning_objectives: bool = Field(default=True, description="Keep same OAs")
    maintain_assessment_rigor: bool = Field(default=True, description="Same evaluation standard")
    
    # Output options
    include_teacher_guide: bool = Field(default=True)
    include_visual_supports: bool = Field(default=True)
    language: str = Field(default="es")

class AdaptContentResponse(BaseModel):
    """Response model for content adaptation"""
    success: bool = Field(..., description="Whether adaptation succeeded")
    adapted_content: Optional[AdaptedContent] = Field(None, description="The adapted content")
    generation_metadata: dict = Field(..., description="Metadata about generation")
    error: Optional[str] = Field(None, description="Error message if failed")

class StreamThought(BaseModel):
    type: str = "thought"
    content: str

class StreamAnswer(BaseModel):
    type: str = "answer"
    content: str

# --- Modelos para Validación de Contenido ---

class ValidationCategory(str, Enum):
    """Categories of validation checks"""
    CURRICULUM_ALIGNMENT = "curriculum_alignment"
    PEDAGOGICAL_QUALITY = "pedagogical_quality"
    CONTENT_ACCURACY = "content_accuracy"
    AGE_APPROPRIATENESS = "age_appropriateness"
    LANGUAGE_QUALITY = "language_quality"
    ACCESSIBILITY = "accessibility"
    SAFETY = "safety"
    BIAS_CHECK = "bias_check"
    COMPLETENESS = "completeness"

class ValidationSeverity(str, Enum):
    """Severity of validation issues"""
    ERROR = "error"          # Must be fixed, blocks publishing
    WARNING = "warning"      # Should be fixed, doesn't block
    INFO = "info"            # Informational, suggestion for improvement

class ValidationStatus(str, Enum):
    """Overall validation status"""
    PASSED = "passed"        # All checks passed
    PASSED_WITH_WARNINGS = "passed_with_warnings"  # Warnings present but publishable
    FAILED = "failed"        # Errors present, cannot publish
    NEEDS_REVIEW = "needs_review"  # Requires human review

class ValidationIssue(BaseModel):
    """A single validation issue found"""
    issue_id: str = Field(..., description="Unique issue identifier")
    category: ValidationCategory = Field(..., description="Category of the issue")
    severity: ValidationSeverity = Field(..., description="Issue severity")
    title: str = Field(..., description="Brief title of the issue")
    description: str = Field(..., description="Detailed description")
    location: Optional[str] = Field(None, description="Where in the content the issue occurs")
    suggestion: str = Field(..., description="How to fix this issue")
    auto_fixable: bool = Field(default=False, description="Whether this can be auto-fixed")

class ValidationCheck(BaseModel):
    """A single validation check performed"""
    check_id: str = Field(..., description="Unique check identifier")
    check_name: str = Field(..., description="Name of the validation check")
    category: ValidationCategory = Field(..., description="Category")
    passed: bool = Field(..., description="Whether the check passed")
    score: float = Field(..., ge=0, le=100, description="Score for this check (0-100)")
    details: str = Field(..., description="Details about the check result")
    issues: List[ValidationIssue] = Field(default=[], description="Issues found by this check")

class ValidationResult(BaseModel):
    """Complete validation result"""
    validation_id: str = Field(..., description="Unique validation ID")
    content_type: str = Field(..., description="Type of content validated")
    
    # Overall status
    status: ValidationStatus = Field(..., description="Overall validation status")
    overall_score: float = Field(..., ge=0, le=100, description="Overall quality score")
    is_publishable: bool = Field(..., description="Whether content can be published")
    
    # Detailed results
    checks_performed: List[ValidationCheck] = Field(..., description="All checks performed")
    issues_found: List[ValidationIssue] = Field(..., description="All issues consolidated")
    
    # Counts
    total_checks: int = Field(..., description="Total number of checks")
    passed_checks: int = Field(..., description="Number of passed checks")
    error_count: int = Field(..., description="Number of errors")
    warning_count: int = Field(..., description="Number of warnings")
    
    # Scores by category
    category_scores: Dict[str, float] = Field(..., description="Scores by category")
    
    # Recommendations
    recommendations: List[str] = Field(..., description="Prioritized recommendations")
    estimated_fix_time_minutes: int = Field(..., description="Estimated time to fix all issues")
    
    # For human review
    requires_human_review: bool = Field(default=False)
    review_priority: str = Field(default="normal", description="low, normal, high, critical")
    review_notes: Optional[str] = Field(None)

class ValidateContentRequest(BaseModel):
    """Request model for content validation"""
    # Content to validate
    content_type: ContentType = Field(..., description="Type of content")
    content: str = Field(..., description="The content to validate (JSON string or markdown)")
    content_id: Optional[str] = Field(None, description="ID if from TPA")
    
    # Context for validation
    grade_level: str = Field(..., description="Target grade level")
    subject: str = Field(..., description="Subject area")
    linked_oas: Optional[List[str]] = Field(None, description="OAs the content should align with")
    
    # Validation configuration
    validation_level: str = Field(default="standard", description="minimal, standard, strict")
    categories_to_check: Optional[List[ValidationCategory]] = Field(
        None,
        description="Categories to validate (default: all)"
    )
    
    # Thresholds
    minimum_score: float = Field(default=70.0, description="Minimum acceptable overall score")
    error_threshold: int = Field(default=0, description="Max errors allowed for pass")
    warning_threshold: int = Field(default=5, description="Max warnings allowed for pass")
    
    # Options
    language: str = Field(default="es")
    include_recommendations: bool = Field(default=True)
    include_fix_suggestions: bool = Field(default=True)

class ValidateContentResponse(BaseModel):
    """Response model for content validation"""
    success: bool = Field(..., description="Whether validation completed")
    result: Optional[ValidationResult] = Field(None, description="Validation result")
    generation_metadata: dict = Field(..., description="Metadata")
    error: Optional[str] = Field(None, description="Error if failed")

# --- Modelos para Generación de Actividades ---

class ActivityType(str, Enum):
    """Types of learning activities"""
    INDIVIDUAL = "individual"
    GROUP = "group"
    PAIR = "pair"
    HANDS_ON = "hands_on"
    INVESTIGATION = "investigation"
    PROJECT = "project"
    GAME = "game"
    SIMULATION = "simulation"
    DISCUSSION = "discussion"
    PRESENTATION = "presentation"

class ActivityResource(BaseModel):
    """Resource needed for an activity"""
    resource_id: str = Field(..., description="Unique resource identifier")
    name: str = Field(..., description="Name of the resource")
    type: str = Field(..., description="Type: material, digital, human, space")
    description: str = Field(..., description="Description of the resource")
    quantity: Optional[int] = Field(None, description="Quantity needed")
    alternative: Optional[str] = Field(None, description="Alternative if not available")

class ActivityStep(BaseModel):
    """A step in the activity"""
    step_number: int = Field(..., description="Step sequence number")
    instruction: str = Field(..., description="Instruction for this step")
    duration_minutes: int = Field(..., description="Duration of this step")
    teacher_role: str = Field(..., description="What the teacher does")
    student_actions: List[str] = Field(..., description="What students do")
    checkpoints: Optional[List[str]] = Field(None, description="Progress checkpoints")

class Activity(BaseModel):
    """Complete activity structure"""
    activity_id: str = Field(..., description="Unique activity identifier")
    title: str = Field(..., description="Activity title")
    description: str = Field(..., description="Activity description")
    activity_type: ActivityType = Field(..., description="Type of activity")
    subject: str = Field(..., description="Subject area")
    grade_level: str = Field(..., description="Grade level")
    
    # Timing
    duration_minutes: int = Field(..., description="Total duration")
    preparation_time_minutes: int = Field(..., description="Prep time needed")
    
    # Learning
    learning_objectives: List[str] = Field(..., description="Specific objectives")
    linked_oas: List[str] = Field(..., description="Linked OA codes")
    skills_developed: List[str] = Field(..., description="Skills practiced")
    
    # Structure
    steps: List[ActivityStep] = Field(..., description="Activity steps")
    resources: List[ActivityResource] = Field(..., description="Required resources")
    
    # Setup
    space_requirements: str = Field(..., description="Space needed")
    group_size: Optional[str] = Field(None, description="Recommended group size")
    prerequisites: List[str] = Field(default=[], description="Prerequisite knowledge/skills")
    
    # Assessment
    success_criteria: List[str] = Field(..., description="Criteria for success")
    observation_checklist: List[str] = Field(..., description="Teacher observation items")
    
    # Extensions
    differentiation_options: Optional[dict] = Field(None, description="Differentiation strategies")
    extension_activities: Optional[List[str]] = Field(None, description="For advanced students")
    simplification_options: Optional[List[str]] = Field(None, description="For struggling students")
    
    # Metadata
    cross_curricular_links: List[str] = Field(default=[], description="Links to other subjects")
    safety_considerations: Optional[str] = Field(None, description="Safety warnings")

class GenerateActivityRequest(BaseModel):
    oa_ids: List[str] = Field(..., description="OA identifiers")
    grade_level: str = Field(..., description="Grade level")
    subject: str = Field(..., description="Subject")
    activity_type: Optional[ActivityType] = Field(None, description="Preferred activity type")
    duration_minutes: int = Field(default=45, description="Target duration")
    group_size: Optional[str] = Field(None, description="Target group size")
    context: Optional[str] = Field(None, description="Additional context")
    available_resources: Optional[List[str]] = Field(None, description="Resources available")
    language: str = Field(default="es", description="Output language")
    include_differentiation: bool = Field(default=True, description="Include differentiation")

class GenerateActivityResponse(BaseModel):
    success: bool = Field(..., description="Whether generation succeeded")
    activity: Optional[Activity] = Field(None, description="The generated activity")
    generation_metadata: dict = Field(..., description="Metadata")
    error: Optional[str] = Field(None, description="Error if failed")

# --- Modelos para Generación de Exámenes ---

class ExamSection(BaseModel):
    """A section of the exam"""
    section_id: str = Field(..., description="Unique section identifier")
    title: str = Field(..., description="Section title")
    instructions: str = Field(..., description="Section instructions")
    questions: List[QuizQuestion] = Field(..., description="Questions in this section")
    total_points: int = Field(..., description="Total points for section")
    time_recommendation_minutes: int = Field(..., description="Recommended time")

class Exam(BaseModel):
    """Complete exam structure"""
    exam_id: str = Field(..., description="Unique exam identifier")
    title: str = Field(..., description="Exam title")
    description: str = Field(..., description="Exam description")
    subject: str = Field(..., description="Subject area")
    grade_level: str = Field(..., description="Grade level")
    
    # Configuration
    total_points: int = Field(..., description="Total exam points")
    time_limit_minutes: int = Field(..., description="Time limit")
    passing_score_percent: int = Field(default=60, description="Passing percentage")
    
    # Structure
    sections: List[ExamSection] = Field(..., description="Exam sections")
    instructions: str = Field(..., description="General instructions")
    
    # Coverage
    linked_oas: List[str] = Field(..., description="Covered OAs")
    oa_coverage: dict = Field(..., description="OA code -> percentage of points")
    bloom_distribution: dict = Field(..., description="Bloom level distribution")
    difficulty_distribution: dict = Field(..., description="Difficulty distribution")
    
    # Metadata
    answer_key: Optional[dict] = Field(None, description="Answer key")
    rubric: Optional[dict] = Field(None, description="Grading rubric")
    accommodations_notes: Optional[str] = Field(None, description="Notes for accommodations")

class GenerateExamRequest(BaseModel):
    oa_ids: List[str] = Field(..., description="OA identifiers")
    grade_level: str = Field(..., description="Grade level")
    subject: str = Field(..., description="Subject")
    exam_title: str = Field(..., description="Title for the exam")
    total_points: int = Field(default=100, description="Total points")
    time_limit_minutes: int = Field(default=60, description="Time limit")
    num_sections: int = Field(default=3, description="Number of sections")
    question_distribution: Optional[dict] = Field(None, description="Type distribution")
    difficulty_distribution: Optional[dict] = Field(None, description="Difficulty distribution")
    include_answer_key: bool = Field(default=True, description="Include answer key")
    include_rubric: bool = Field(default=True, description="Include rubric")
    language: str = Field(default="es", description="Output language")

class GenerateExamResponse(BaseModel):
    success: bool = Field(..., description="Whether generation succeeded")
    exam: Optional[Exam] = Field(None, description="The generated exam")
    generation_metadata: dict = Field(..., description="Metadata")
    error: Optional[str] = Field(None, description="Error if failed")

# --- Modelos para Reforzamiento ---

class ReinforcementType(str, Enum):
    """Types of reinforcement materials"""
    CONCEPT_REVIEW = "concept_review"
    PRACTICE_EXERCISES = "practice_exercises"
    VISUAL_GUIDE = "visual_guide"
    WORKED_EXAMPLES = "worked_examples"
    FLASHCARDS = "flashcards"
    SUMMARY_SHEET = "summary_sheet"
    SCAFFOLDED_WORKSHEET = "scaffolded_worksheet"

class ReinforcementMaterial(BaseModel):
    """A single reinforcement material"""
    material_id: str = Field(..., description="Unique material identifier")
    type: ReinforcementType = Field(..., description="Type of material")
    title: str = Field(..., description="Material title")
    content: str = Field(..., description="Markdown content")
    estimated_time_minutes: int = Field(..., description="Estimated time")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")

class ReinforcementPlan(BaseModel):
    """Complete reinforcement plan"""
    plan_id: str = Field(..., description="Unique plan identifier")
    title: str = Field(..., description="Plan title")
    description: str = Field(..., description="Plan description")
    subject: str = Field(..., description="Subject area")
    grade_level: str = Field(..., description="Grade level")
    
    # Target
    target_oas: List[str] = Field(..., description="Targeted OAs")
    identified_gaps: List[str] = Field(..., description="Gaps addressed")
    prerequisite_skills: List[str] = Field(..., description="Prerequisites needed")
    
    # Materials
    materials: List[ReinforcementMaterial] = Field(..., description="Generated materials")
    
    # Sequence
    recommended_sequence: List[str] = Field(..., description="Order of materials")
    estimated_total_time_minutes: int = Field(..., description="Total time")
    
    # Support
    teacher_guidance: str = Field(..., description="Guide for teacher")
    parent_guidance: Optional[str] = Field(None, description="Guide for parents")
    self_assessment_checklist: List[str] = Field(..., description="Student checklist")
    
    # Progress tracking
    mastery_indicators: List[str] = Field(..., description="Signs of mastery")
    next_steps_on_success: str = Field(..., description="What to do if successful")
    next_steps_on_struggle: str = Field(..., description="What to do if struggling")

class GenerateReinforcementRequest(BaseModel):
    oa_ids: List[str] = Field(..., description="OA identifiers")
    grade_level: str = Field(..., description="Grade level")
    subject: str = Field(..., description="Subject")
    identified_gaps: Optional[List[str]] = Field(None, description="Specific gaps to address")
    student_performance_context: Optional[str] = Field(None, description="Context on performance")
    reinforcement_types: Optional[List[ReinforcementType]] = Field(None, description="Preferred types")
    num_materials: int = Field(default=5, description="Number of materials")
    difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Target difficulty")
    include_parent_guidance: bool = Field(default=False, description="Include parent guide")
    language: str = Field(default="es", description="Output language")

class GenerateReinforcementResponse(BaseModel):
    success: bool = Field(..., description="Whether generation succeeded")
    reinforcement_plan: Optional[ReinforcementPlan] = Field(None, description="The generated plan")
    generation_metadata: dict = Field(..., description="Metadata")
    error: Optional[str] = Field(None, description="Error if failed")

# --- Modelos para Resúmenes y Estudio ---

class SummaryFormat(str, Enum):
    """Output formats for summaries"""
    NARRATIVE = "narrative"        # Continuous text
    BULLET_POINTS = "bullet_points"  # Key points
    CONCEPT_MAP = "concept_map"    # Relationships
    CORNELL_NOTES = "cornell_notes"  # Cornell format
    FLASHCARD_SET = "flashcard_set"  # Q&A pairs

class Flashcard(BaseModel):
    """A single flashcard"""
    card_id: str
    front: str  # Question/term
    back: str   # Answer/definition
    category: Optional[str] = None
    difficulty: DifficultyLevel

class ConceptRelation(BaseModel):
    """Relationship between concepts for concept maps"""
    from_concept: str
    to_concept: str
    relationship_type: str  # "causes", "contains", "requires", "leads_to", etc.
    description: Optional[str] = None

class UnitSummary(BaseModel):
    """Complete unit summary"""
    summary_id: str
    title: str
    subject: str
    grade_level: str
    unit_name: str
    
    # Summary content
    format: SummaryFormat
    content: str  # Main content (markdown)
    
    # Structured elements
    key_concepts: List[str]
    key_vocabulary: List[dict]  # [{term, definition}]
    main_ideas: List[str]
    
    # For concept maps
    concept_relations: Optional[List[ConceptRelation]] = None
    
    # For flashcards
    flashcards: Optional[List[Flashcard]] = None
    
    # Study aids
    study_questions: List[str]
    common_misconceptions: List[str]
    real_world_connections: List[str]
    
    # Review
    quick_review_checklist: List[str]
    self_assessment_questions: List[str]
    
    # Metadata
    linked_oas: List[str]
    estimated_study_time_minutes: int
    prerequisites: List[str]

class GenerateSummaryRequest(BaseModel):
    """Request model for summary generation"""
    oa_ids: List[str] = Field(..., description="OA identifiers for the unit")
    grade_level: str
    subject: str
    unit_name: str
    
    # Format options
    format: SummaryFormat = Field(default=SummaryFormat.BULLET_POINTS)
    include_flashcards: bool = Field(default=True)
    num_flashcards: int = Field(default=10, ge=5, le=30)
    include_concept_map: bool = Field(default=False)
    
    # Content options
    difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM)
    language: str = Field(default="es")
    context: Optional[str] = None

class GenerateSummaryResponse(BaseModel):
    """Response model for summary generation"""
    success: bool
    summary: Optional[UnitSummary] = None
    generation_metadata: dict
    error: Optional[str] = None

# --- Modelos para Tutor IA ---

class TutorRole(str, Enum):
    """Role/mode for the tutor"""
    EXPLAIN = "explain"        # Explain concepts
    PRACTICE = "practice"      # Guide through practice
    QUESTION = "question"      # Socratic questioning
    ENCOURAGE = "encourage"    # Motivational support
    REVIEW = "review"          # Review material

class ChatMessage(BaseModel):
    """A single chat message"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TutorContext(BaseModel):
    """Context for tutoring session"""
    student_grade_level: str
    subject: str
    current_topic: Optional[str] = None
    linked_oas: Optional[List[str]] = None
    student_nee: Optional[List[str]] = None  # NEE types if applicable
    learning_style: Optional[str] = None  # visual, auditory, kinesthetic
    difficulty_preference: DifficultyLevel = DifficultyLevel.MEDIUM

class TutorChatRequest(BaseModel):
    """Request model for tutor chat"""
    message: str = Field(..., description="Student's message/question")
    context: TutorContext
    
    # Session management
    session_id: Optional[str] = Field(None, description="Existing session ID for continuity")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Previous messages in conversation (max 10)"
    )
    
    # Tutor behavior
    tutor_role: TutorRole = Field(default=TutorRole.EXPLAIN)
    response_style: str = Field(default="friendly", description="friendly, formal, playful")
    
    # Options
    language: str = Field(default="es")
    max_response_length: int = Field(default=500, description="Max words in response")
    include_examples: bool = Field(default=True)
    include_follow_up_questions: bool = Field(default=True)

class TutorResponse(BaseModel):
    """A single tutor response"""
    message: str
    examples: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None
    resources: Optional[List[str]] = None
    encouragement: Optional[str] = None

class TutorChatResponse(BaseModel):
    """Response model for tutor chat"""
    success: bool
    response: Optional[TutorResponse] = None
    session_id: str
    conversation_summary: Optional[str] = None
    topics_covered: List[str] = []
    generation_metadata: dict
    error: Optional[str] = None

# --- Modelos para Autenticación y Usuarios ---

class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    is_active: bool

class UserRoleUpdate(BaseModel):
    role: str

class User(UserBase):
    id: int
    is_active: bool
    role: str

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

# --- Modelos para Batch Processing ---

class BatchContentType(str, Enum):
    """Types of content that can be batch generated"""
    QUIZ = "quiz"
    ACTIVITY = "activity"
    EXAM = "exam"
    REINFORCEMENT = "reinforcement"
    LESSON = "lesson"

class BatchItemRequest(BaseModel):
    """A single item in a batch request"""
    item_id: str = Field(..., description="Unique identifier for this item")
    oa_ids: List[str] = Field(..., description="OA identifiers")
    grade_level: str
    subject: str
    # Additional fields depend on content type - passed through to specific generator

class BatchGenerateRequest(BaseModel):
    """Request model for batch generation"""
    content_type: BatchContentType = Field(..., description="Type of content to generate")
    items: List[dict] = Field(..., description="Items to generate (each with item_id and content-specific fields)")
    
    # Webhook configuration
    webhook_url: Optional[str] = Field(None, description="URL for progress/completion notifications")
    webhook_secret: Optional[str] = Field(None, description="Secret for webhook signature")
    
    # Options
    priority: str = Field(default="normal", description="low, normal, high")

class BatchJobInfo(BaseModel):
    """Information about a batch job"""
    job_id: str
    status: str
    content_type: str
    total_items: int
    completed_items: int
    failed_items: int
    progress_percent: float
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class BatchGenerateResponse(BaseModel):
    """Response model for batch generation request"""
    success: bool
    job: Optional[BatchJobInfo] = None
    message: str
    error: Optional[str] = None

class BatchStatusResponse(BaseModel):
    """Response for batch job status"""
    job: BatchJobInfo
    results: Optional[List[dict]] = None  # Only included if completed

# --- Modelos para Analítica y Dashboards ---

class UserCostSummary(BaseModel):
    username: str
    total_cost: float
    total_plannings: int
    is_active: bool
    role: str

    class Config:
        from_attributes = True

class AdminDashboardStats(BaseModel):
    total_users: int
    total_system_cost: float
    total_system_plannings: int
    users_summary: list[UserCostSummary]

class PlanningLogResponse(BaseModel):
    id: int
    oa_codigo: str
    cost: float
    timestamp: datetime

    class Config:
        from_attributes = True

class PlanningLogDetailResponse(PlanningLogResponse):
    input_tokens: int
    output_tokens: int
    thought_tokens: int
    plan_request_data: PlanRequest
    plan_markdown: str