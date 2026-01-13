import google.generativeai as genai
from api.core.config import settings
from api.models import (
    StructuredPlanRequest, StructuredLesson, GenerateQuizRequest, Quiz,
    AdaptContentRequest, AdaptedContent, NEEType,
    ValidateContentRequest, ValidationResult, ValidationStatus, ValidationSeverity,
    GenerateActivityRequest, Activity, GenerateExamRequest, Exam,
    GenerateReinforcementRequest, ReinforcementPlan,
    GenerateSummaryRequest, UnitSummary, SummaryFormat,
    TutorChatRequest, TutorResponse, TutorRole
)
from api.services.schema_utils import clean_schema_for_gemini
import json
import uuid
from typing import Optional
from datetime import datetime

class ContentGenerationService:
    """Service for generating structured educational content using Gemini"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def generate_structured_lesson(
        self, 
        request: StructuredPlanRequest,
        curriculum_data: dict  # OA data from curriculum service
    ) -> StructuredLesson:
        """
        Generate a structured lesson plan based on curriculum OAs.
        Returns a fully structured StructuredLesson object.
        """
        # Build the prompt with curriculum context
        prompt = self._build_lesson_prompt(request, curriculum_data)
        
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=clean_schema_for_gemini(StructuredLesson.model_json_schema())
        )
        
        # Generate with Gemini
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        # Parse and validate response
        lesson_data = json.loads(response.text)
        
        # Add generated IDs if missing
        if 'lesson_id' not in lesson_data:
            lesson_data['lesson_id'] = f"lesson_{uuid.uuid4().hex[:8]}"
        
        return StructuredLesson(**lesson_data)
    
    async def generate_quiz(
        self,
        request: GenerateQuizRequest,
        curriculum_data: dict
    ) -> Quiz:
        """
        Generate a quiz based on curriculum OAs.
        Returns a fully structured Quiz object.
        """
        prompt = self._build_quiz_prompt(request, curriculum_data)
        
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=clean_schema_for_gemini(Quiz.model_json_schema())
        )
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        quiz_data = json.loads(response.text)
        quiz_data['quiz_id'] = f"quiz_{uuid.uuid4().hex[:8]}"
        
        # Calculate totals
        quiz_data['total_points'] = sum(q.get('points', 1) for q in quiz_data.get('questions', []))
        
        return Quiz(**quiz_data)

    async def generate_activity(
        self,
        request: GenerateActivityRequest,
        curriculum_data: dict
    ) -> Activity:
        """Generate an interactive learning activity"""
        prompt = self._build_activity_prompt(request, curriculum_data)
        
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=clean_schema_for_gemini(Activity.model_json_schema())
        )
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        activity_data = json.loads(response.text)
        activity_data['activity_id'] = f"act_{uuid.uuid4().hex[:8]}"
        
        return Activity(**activity_data)

    async def generate_exam(
        self,
        request: GenerateExamRequest,
        curriculum_data: dict
    ) -> Exam:
        """Generate a summative exam"""
        prompt = self._build_exam_prompt(request, curriculum_data)
        
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=clean_schema_for_gemini(Exam.model_json_schema())
        )
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        exam_data = json.loads(response.text)
        exam_data['exam_id'] = f"exam_{uuid.uuid4().hex[:8]}"
        
        return Exam(**exam_data)

    async def generate_reinforcement(
        self,
        request: GenerateReinforcementRequest,
        curriculum_data: dict
    ) -> ReinforcementPlan:
        """Generate reinforcement materials for struggling students"""
        prompt = self._build_reinforcement_prompt(request, curriculum_data)
        
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=clean_schema_for_gemini(ReinforcementPlan.model_json_schema())
        )
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        plan_data = json.loads(response.text)
        plan_data['plan_id'] = f"reinf_{uuid.uuid4().hex[:8]}"
        
        return ReinforcementPlan(**plan_data)

    async def generate_summary(
        self,
        request: GenerateSummaryRequest,
        curriculum_data: dict
    ) -> UnitSummary:
        """Generate a unit summary with optional flashcards and concept maps"""
        prompt = self._build_summary_prompt(request, curriculum_data)
        
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=clean_schema_for_gemini(UnitSummary.model_json_schema())
        )
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        summary_data = json.loads(response.text)
        summary_data['summary_id'] = f"summary_{uuid.uuid4().hex[:8]}"
        
        return UnitSummary(**summary_data)

    async def tutor_chat(
        self,
        request: TutorChatRequest,
        curriculum_data: Optional[dict] = None
    ) -> TutorResponse:
        """
        Generate a tutor response to student query.
        Maintains conversational context for natural interaction.
        """
        prompt = self._build_tutor_prompt(request, curriculum_data)
        
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=clean_schema_for_gemini(TutorResponse.model_json_schema())
        )
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        return TutorResponse(**json.loads(response.text))

    async def adapt_content_for_nee(
        self,
        request: AdaptContentRequest
    ) -> AdaptedContent:
        """
        Adapt educational content for students with special educational needs.
        Returns fully structured AdaptedContent with all modifications and guidance.
        """
        prompt = self._build_adaptation_prompt(request)
        
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=clean_schema_for_gemini(AdaptedContent.model_json_schema())
        )
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        adapted_data = json.loads(response.text)
        adapted_data['adapted_content_id'] = f"adapted_{uuid.uuid4().hex[:8]}"
        adapted_data['original_content_id'] = request.original_content_id or "external"
        
        return AdaptedContent(**adapted_data)

    async def validate_content(
        self,
        request: ValidateContentRequest,
        curriculum_data: Optional[dict] = None
    ) -> ValidationResult:
        """
        Validate educational content against quality criteria.
        Returns comprehensive validation results with issues and recommendations.
        """
        prompt = self._build_validation_prompt(request, curriculum_data)
        
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=clean_schema_for_gemini(ValidationResult.model_json_schema())
        )
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        result_data = json.loads(response.text)
        result_data['validation_id'] = f"val_{uuid.uuid4().hex[:8]}"
        
        # Calculate derived fields
        result = ValidationResult(**result_data)
        
        # Ensure counts are correct
        result.error_count = len([i for i in result.issues_found if i.severity == ValidationSeverity.ERROR])
        result.warning_count = len([i for i in result.issues_found if i.severity == ValidationSeverity.WARNING])
        result.total_checks = len(result.checks_performed)
        result.passed_checks = len([c for c in result.checks_performed if c.passed])
        
        # Determine publishability
        result.is_publishable = (
            result.error_count <= request.error_threshold and
            result.warning_count <= request.warning_threshold and
            result.overall_score >= request.minimum_score
        )
        
        # Determine status
        if result.error_count > 0:
            result.status = ValidationStatus.FAILED
        elif result.warning_count > request.warning_threshold:
            result.status = ValidationStatus.NEEDS_REVIEW
        elif result.warning_count > 0:
            result.status = ValidationStatus.PASSED_WITH_WARNINGS
        else:
            result.status = ValidationStatus.PASSED
        
        return result

    def _build_validation_prompt(self, request: ValidateContentRequest, curriculum_data: Optional[dict]) -> str:
        """Build prompt for content validation"""
        
        oas_text = ""
        if curriculum_data and curriculum_data.get('oas'):
            oas_text = "## OAs que debe cubrir:\n" + "\n".join([
                f"- {oa['codigo']}: {oa['descripcion']}"
                for oa in curriculum_data.get('oas', [])
            ])
        
        categories_text = ""
        if request.categories_to_check:
            categories_text = f"Categorías a validar: {', '.join([c.value for c in request.categories_to_check])}"
        else:
            categories_text = "Validar todas las categorías: alineación curricular, calidad pedagógica, precisión del contenido, apropiado para la edad, calidad del lenguaje, accesibilidad, seguridad, sesgos, completitud"
        
        validation_criteria = {
            "minimal": "Solo errores críticos y problemas de seguridad",
            "standard": "Errores, advertencias principales, y sugerencias básicas",
            "strict": "Validación exhaustiva incluyendo mejoras de estilo y optimizaciones"
        }
        
        prompt = f"""
Eres un experto en calidad de contenido educativo y currículum nacional chileno. Valida el siguiente contenido educativo.

## Contenido a Validar
Tipo: {request.content_type.value}
Nivel: {request.grade_level}
Asignatura: {request.subject}

### Contenido:
{request.content}

{oas_text}

## Criterios de Validación
Nivel: {request.validation_level} - {validation_criteria[request.validation_level]}
{categories_text}

## Umbrales de Calidad
- Puntaje mínimo requerido: {request.minimum_score}
- Máximo errores permitidos: {request.error_threshold}
- Máximo advertencias permitidas: {request.warning_threshold}

## Instrucciones de Validación

### 1. Alineación Curricular (curriculum_alignment)
- ¿El contenido cubre los OAs especificados?
- ¿Los objetivos de aprendizaje son apropiados para el nivel?
- ¿Hay coherencia con las bases curriculares chilenas?

### 2. Calidad Pedagógica (pedagogical_quality)
- ¿La secuencia didáctica es lógica?
- ¿Las actividades promueven el aprendizaje activo?
- ¿Hay evaluación formativa integrada?
- ¿Se consideran diferentes estilos de aprendizaje?

### 3. Precisión del Contenido (content_accuracy)
- ¿La información es factualmente correcta?
- ¿Los conceptos están bien explicados?
- ¿No hay errores técnicos o científicos?

### 4. Apropiado para la Edad (age_appropriateness)
- ¿El vocabulario es adecuado para el nivel?
- ¿Los ejemplos son relevantes para la edad?
- ¿La complejidad es apropiada?

### 5. Calidad del Lenguaje (language_quality)
- ¿El español es correcto y claro?
- ¿No hay errores gramaticales u ortográficos?
- ¿Las instrucciones son comprensibles?

### 6. Accesibilidad (accessibility)
- ¿El contenido puede ser accedido por estudiantes con NEE?
- ¿Hay descripciones para elementos visuales?
- ¿Se evita depender solo de color o audio?

### 7. Seguridad (safety)
- ¿No hay contenido inapropiado o peligroso?
- ¿Las actividades son seguras para estudiantes?
- ¿Se respetan normativas de protección de menores?

### 8. Sesgos (bias_check)
- ¿El contenido es inclusivo y diverso?
- ¿No hay estereotipos de género, raza, o clase?
- ¿Representa diversidad cultural chilena?

### 9. Completitud (completeness)
- ¿El contenido está completo?
- ¿Hay todos los elementos requeridos?
- ¿No faltan instrucciones o recursos?

## Formato de Respuesta
Para cada check realizado, proporciona:
- Si pasó o no
- Puntaje (0-100)
- Detalles de la evaluación
- Issues encontrados (si los hay) con severidad y sugerencia de fix

{"Incluye recomendaciones priorizadas para mejorar" if request.include_recommendations else ""}
{"Incluye sugerencias específicas de cómo arreglar cada issue" if request.include_fix_suggestions else ""}

Genera el resultado de validación en formato JSON estructurado.
"""
        return prompt

    def _build_adaptation_prompt(self, request: AdaptContentRequest) -> str:
        """Build prompt for NEE content adaptation"""
        nee_descriptions = {
            NEEType.DYSLEXIA: "Dificultad con lectura, decodificación y ortografía. Necesita: textos simplificados, apoyo visual, tiempo extra.",
            NEEType.DYSCALCULIA: "Dificultad con conceptos matemáticos y números. Necesita: manipulativos, visualizaciones, pasos explícitos.",
            NEEType.ADHD: "Dificultad con atención y concentración. Necesita: instrucciones breves, descansos, contenido dividido.",
            NEEType.AUTISM_SPECTRUM: "Diferencias en comunicación social. Necesita: rutinas claras, instrucciones explícitas, apoyo sensorial.",
            NEEType.VISUAL_IMPAIRMENT: "Dificultad visual. Necesita: textos grandes, alto contraste, descripciones de audio.",
            NEEType.HEARING_IMPAIRMENT: "Dificultad auditiva. Necesita: apoyo visual, subtítulos, instrucciones escritas.",
            NEEType.MILD_INTELLECTUAL: "Ritmo de aprendizaje más lento. Necesita: contenido simplificado, más ejemplos, repetición.",
            NEEType.GIFTED: "Alto potencial. Necesita: desafíos adicionales, profundización, proyectos extendidos.",
            # Add more as needed
        }
        
        nee_info = "\n".join([
            f"- {nee.value}: {nee_descriptions.get(nee, 'Requiere adaptaciones personalizadas')}"
            for nee in request.nee_types
        ])
        
        strengths_text = ""
        if request.student_strengths:
            strengths_text = f"Fortalezas del estudiante: {', '.join(request.student_strengths)}"
        
        challenges_text = ""
        if request.student_challenges:
            challenges_text = f"Desafíos específicos: {', '.join(request.student_challenges)}"
        
        previous_strategies = ""
        if request.previous_successful_strategies:
            previous_strategies = f"Estrategias que han funcionado antes: {', '.join(request.previous_successful_strategies)}"
        
        prompt = f"""
Eres un especialista en educación inclusiva y adaptaciones curriculares para estudiantes con NEE (Necesidades Educativas Especiales) en Chile.

## Contenido Original a Adaptar
Tipo: {request.content_type.value}
Nivel: {request.student_grade_level}
{f"Edad del estudiante: {request.student_age} años" if request.student_age else ""}

### Contenido:
{request.original_content}

## Perfil NEE del Estudiante
Nivel de adaptación requerido: {request.adaptation_level.value}

Necesidades identificadas:
{nee_info}

{strengths_text}
{challenges_text}
{previous_strategies}

## Requisitos de la Adaptación
- {"Mantener los mismos objetivos de aprendizaje" if request.maintain_learning_objectives else "Se pueden modificar objetivos"}
- {"Mantener el rigor de evaluación" if request.maintain_assessment_rigor else "Se puede reducir la dificultad"}
- {"Incluir guía para el docente" if request.include_teacher_guide else ""}
- {"Incluir apoyos visuales" if request.include_visual_supports else ""}
- Idioma: {"Español" if request.language == "es" else "English"}

## Instrucciones
1. Analiza el contenido original y las NEE del estudiante
2. Aplica estrategias de adaptación basadas en evidencia para cada NEE
3. Mantén la esencia del contenido mientras lo haces accesible
4. Proporciona el contenido adaptado en formato claro
5. Incluye todas las adaptaciones visuales, cognitivas, temporales y de apoyo necesarias
6. Genera notas detalladas para el docente sobre implementación
7. Crea una lista de verificación de implementación
8. Define indicadores de éxito para evaluar si la adaptación funciona
9. Calcula un puntaje de accesibilidad (0-100)

El contenido adaptado debe ser:
- Accesible para el estudiante según su perfil
- Respetuoso de su dignidad
- Desafiante pero alcanzable
- Alineado con el currículum nacional

Genera la adaptación en formato JSON estructurado.
"""
        return prompt

    def _build_quiz_prompt(self, request: GenerateQuizRequest, curriculum_data: dict) -> str:
        """Build prompt for quiz generation"""
        oas_text = "\n".join([
            f"- {oa['codigo']}: {oa['descripcion']}"
            for oa in curriculum_data.get('oas', [])
        ])
        
        question_types_text = ""
        if request.question_types:
            question_types_text = f"Tipos de preguntas permitidos: {', '.join([qt.value for qt in request.question_types])}"
        else:
            question_types_text = "Usar variedad de tipos: selección múltiple, verdadero/falso, respuesta corta, completar, parear, ordenar"
        
        difficulty_text = ""
        if request.difficulty_distribution:
            difficulty_text = f"Distribución de dificultad: {request.difficulty_distribution}"
        else:
            difficulty_text = "Distribución equilibrada de dificultad (fácil, medio, difícil)"
        
        prompt = f"""
Eres un experto en evaluación educativa chilena. Genera un quiz estructurado siguiendo el currículum nacional.

## Contexto del Currículum
Asignatura: {request.subject}
Nivel: {request.grade_level}

## Objetivos de Aprendizaje (OAs) a evaluar:
{oas_text}

## Requisitos del Quiz
- Número de preguntas: {request.num_questions}
- {question_types_text}
- {difficulty_text}
- Idioma: {"Español" if request.language == "es" else "English"}
{f"- Niveles de Bloom objetivo: {[bl.value for bl in request.bloom_levels]}" if request.bloom_levels else ""}
{f"- Límite de tiempo: {request.time_limit_minutes} minutos" if request.time_limit_minutes else ""}
{f"- Contexto adicional: {request.context}" if request.context else ""}

## Instrucciones
1. Cada pregunta debe evaluar un OA específico
2. Incluye variedad en tipos de preguntas
3. Las preguntas de selección múltiple deben tener 4 opciones
4. {"Incluye pistas para cada pregunta" if request.include_hints else "No incluir pistas"}
5. {"Incluye explicación de la respuesta correcta" if request.include_explanations else "No incluir explicaciones"}
6. Asegura que las preguntas sean claras y sin ambigüedad
7. Las respuestas incorrectas deben ser plausibles pero claramente incorrectas

Genera el quiz en formato JSON estructurado.
"""
        return prompt

    def _build_lesson_prompt(self, request: StructuredPlanRequest, curriculum_data: dict) -> str:
        """Build the prompt for lesson generation"""
        oas_text = "\n".join([
            f"- {oa['codigo']}: {oa['descripcion']}"
            for oa in curriculum_data.get('oas', [])
        ])
        
        prompt = f"""
Eres un experto pedagogo chileno. Genera una planificación de clase estructurada siguiendo el currículum nacional de Chile.

## Contexto del Currículum
Asignatura: {request.subject}
Nivel: {request.grade_level}

## Objetivos de Aprendizaje (OAs) a cubrir:
{oas_text}

## Requisitos de la Clase
- Duración total: {request.duration_minutes} minutos
- Idioma: {"Español" if request.language == "es" else "English"}
{f"- Contexto adicional: {request.context}" if request.context else ""}

## Instrucciones
1. Diseña una clase completa con inicio, desarrollo y cierre
2. Incluye actividades específicas con tiempos y acciones del profesor/estudiante
3. Define objetivos medibles con criterios de éxito
4. {"Incluye notas de diferenciación para distintos ritmos de aprendizaje" if request.include_differentiation else ""}
5. {"Incluye rúbrica de evaluación" if request.include_assessment_rubric else ""}

Genera la planificación en formato JSON estructurado.
"""
        return prompt

    def _build_activity_prompt(self, request: GenerateActivityRequest, curriculum_data: dict) -> str:
        """Build prompt for activity generation"""
        oas_text = "\n".join([
            f"- {oa['codigo']}: {oa['descripcion']}"
            for oa in curriculum_data.get('oas', [])
        ])
        
        prompt = f"""
Eres un experto en didáctica y metodologías activas. Genera una actividad de aprendizaje detallada y atractiva.

## Contexto
Asignatura: {request.subject}
Nivel: {request.grade_level}
OAs:
{oas_text}

## Requisitos
- Duración: {request.duration_minutes} minutos
- Tipo preferido: {request.activity_type.value if request.activity_type else "El más adecuado para el OA"}
- Idioma: {"Español" if request.language == "es" else "English"}
{f"- Tamaño de grupo: {request.group_size}" if request.group_size else ""}
{f"- Recursos disponibles: {', '.join(request.available_resources)}" if request.available_resources else ""}
{f"- Contexto: {request.context}" if request.context else ""}

## Instrucciones
1. Crea una actividad paso a paso con tiempos claros
2. Define roles claros para docente y estudiantes
3. Especifica recursos necesarios (materiales, digitales, espacios)
4. Incluye criterios de éxito y lista de cotejo
5. {"Incluye opciones de diferenciación y extensión" if request.include_differentiation else ""}

Genera la actividad en formato JSON estructurado.
"""
        return prompt

    def _build_exam_prompt(self, request: GenerateExamRequest, curriculum_data: dict) -> str:
        """Build prompt for exam generation"""
        oas_text = "\n".join([
            f"- {oa['codigo']}: {oa['descripcion']}"
            for oa in curriculum_data.get('oas', [])
        ])
        
        dist_text = ""
        if request.question_distribution:
            dist_text = f"Distribución de preguntas: {request.question_distribution}"
        
        diff_text = ""
        if request.difficulty_distribution:
            diff_text = f"Dificultad: {request.difficulty_distribution}"
            
        prompt = f"""
Eres un experto en evaluación sumativa. Genera un examen completo y equilibrado.

## Contexto
Título: {request.exam_title}
Asignatura: {request.subject}
Nivel: {request.grade_level}
OAs a evaluar:
{oas_text}

## Configuración
- Puntos totales: {request.total_points}
- Tiempo límite: {request.time_limit_minutes} minutos
- Secciones: {request.num_sections}
- Idioma: {"Español" if request.language == "es" else "English"}
{dist_text}
{diff_text}

## Instrucciones
1. Crea un examen con secciones claras e instrucciones precisas
2. Asegura cobertura balanceada de los OAs
3. Incluye variedad de niveles cognitivos (Bloom)
4. {"Genera pauta de corrección (respuestas)" if request.include_answer_key else ""}
5. {"Incluye rúbrica de evaluación" if request.include_rubric else ""}

Genera el examen en formato JSON estructurado.
"""
        return prompt

    def _build_reinforcement_prompt(self, request: GenerateReinforcementRequest, curriculum_data: dict) -> str:
        """Build prompt for reinforcement generation"""
        oas_text = "\n".join([
            f"- {oa['codigo']}: {oa['descripcion']}"
            for oa in curriculum_data.get('oas', [])
        ])
        
        gaps_text = ""
        if request.identified_gaps:
            gaps_text = f"Brechas identificadas: {', '.join(request.identified_gaps)}"
            
        types_text = ""
        if request.reinforcement_types:
            types_text = f"Tipos de material preferidos: {', '.join([t.value for t in request.reinforcement_types])}"
            
        prompt = f"""
Eres un especialista en remediación y apoyo pedagógico. Genera un plan de reforzamiento personalizado.

## Contexto
Asignatura: {request.subject}
Nivel: {request.grade_level}
OAs a reforzar:
{oas_text}

{gaps_text}
{f"Contexto de desempeño: {request.student_performance_context}" if request.student_performance_context else ""}

## Requisitos
- Cantidad de materiales: {request.num_materials}
- Nivel de dificultad inicial: {request.difficulty_level.value}
- Idioma: {"Español" if request.language == "es" else "English"}
{types_text}

## Instrucciones
1. Diseña una secuencia lógica de reforzamiento
2. Crea materiales variados (repaso, práctica, visuales)
3. Incluye guía para el docente sobre cómo usar los materiales
4. {"Incluye guía para padres/apoderados" if request.include_parent_guidance else ""}
5. Define indicadores claros de superación de las brechas

Genera el plan de reforzamiento en formato JSON estructurado.
"""
        return prompt

    def _build_summary_prompt(self, request: GenerateSummaryRequest, curriculum_data: dict) -> str:
        """Build prompt for summary generation"""
        oas_text = "\n".join([
            f"- {oa['codigo']}: {oa['descripcion']}"
            for oa in curriculum_data.get('oas', [])
        ])
        
        format_instructions = {
            SummaryFormat.NARRATIVE: "Redacta un resumen continuo y coherente",
            SummaryFormat.BULLET_POINTS: "Organiza el resumen en viñetas claras y concisas",
            SummaryFormat.CONCEPT_MAP: "Estructura el resumen mostrando relaciones entre conceptos",
            SummaryFormat.CORNELL_NOTES: "Usa el formato Cornell: notas principales, preguntas al margen, resumen final",
            SummaryFormat.FLASHCARD_SET: "Enfócate en crear tarjetas de estudio efectivas"
        }
        
        prompt = f"""
Eres un tutor experto que crea resúmenes de estudio efectivos para estudiantes chilenos.

## Unidad a Resumir
Asignatura: {request.subject}
Nivel: {request.grade_level}
Unidad: {request.unit_name}

## Objetivos de Aprendizaje (OAs):
{oas_text}

## Formato Solicitado
{format_instructions[request.format]}

## Requisitos
- Nivel de dificultad: {request.difficulty_level.value}
- Idioma: {"Español" if request.language == "es" else "English"}
{f"- Incluir {request.num_flashcards} flashcards" if request.include_flashcards else ""}
{f"- Incluir mapa conceptual con relaciones" if request.include_concept_map else ""}
{f"- Contexto adicional: {request.context}" if request.context else ""}

## Instrucciones
1. Identifica los conceptos clave de la unidad
2. Extrae el vocabulario esencial con definiciones claras
3. Sintetiza las ideas principales
4. Crea preguntas de estudio que verifiquen comprensión
5. Anticipa y corrige concepciones erróneas comunes
6. Conecta con aplicaciones del mundo real
7. Incluye una lista de verificación de repaso rápido
8. Estima el tiempo de estudio necesario

El resumen debe ser claro, completo y útil para que un estudiante repase antes de una evaluación.

Genera el resumen en formato JSON estructurado.
"""
        return prompt

    def _build_tutor_prompt(self, request: TutorChatRequest, curriculum_data: Optional[dict]) -> str:
        """Build prompt for tutor chat"""
        
        # Build conversation history
        history_text = ""
        if request.conversation_history:
            history_text = "\n## Conversación Previa:\n"
            for msg in request.conversation_history[-10:]:  # Last 10 messages
                history_text += f"{msg.role.upper()}: {msg.content}\n"
        
        # NEE adaptations
        nee_text = ""
        if request.context.student_nee:
            nee_text = f"\nEl estudiante tiene NEE: {', '.join(request.context.student_nee)}. Adapta tu respuesta apropiadamente."
        
        # Curriculum context
        oas_text = ""
        if curriculum_data and curriculum_data.get('oas'):
            oas_text = "\n## OAs Relevantes:\n" + "\n".join([
                f"- {oa['codigo']}: {oa['descripcion']}"
                for oa in curriculum_data.get('oas', [])[:5]  # Limit to 5 OAs
            ])
        
        role_instructions = {
            TutorRole.EXPLAIN: "Explica el concepto de manera clara y didáctica",
            TutorRole.PRACTICE: "Guía al estudiante a través de ejercicios prácticos paso a paso",
            TutorRole.QUESTION: "Usa el método socrático - haz preguntas que lleven al estudiante a descubrir la respuesta",
            TutorRole.ENCOURAGE: "Sé motivador y positivo, celebra los logros y normaliza los errores",
            TutorRole.REVIEW: "Ayuda a repasar y consolidar lo aprendido"
        }
        
        style_instructions = {
            "friendly": "Usa un tono amigable y cercano, como un hermano mayor",
            "formal": "Mantén un tono profesional pero accesible",
            "playful": "Sé divertido y usa ejemplos creativos, especialmente para niños pequeños"
        }
        
        prompt = f"""
Eres un tutor IA amable y paciente para estudiantes chilenos. Tu nombre es "Profe TPA".

## Perfil del Estudiante
- Nivel: {request.context.student_grade_level}
- Asignatura: {request.context.subject}
{f"- Tema actual: {request.context.current_topic}" if request.context.current_topic else ""}
{f"- Estilo de aprendizaje preferido: {request.context.learning_style}" if request.context.learning_style else ""}
{nee_text}

{oas_text}

{history_text}

## Mensaje del Estudiante
"{request.message}"

## Tu Rol
{role_instructions[request.tutor_role]}
{style_instructions.get(request.response_style, style_instructions["friendly"])}

## Instrucciones
1. Responde al mensaje del estudiante de manera {request.response_style}
2. Mantén tu respuesta en máximo {request.max_response_length} palabras
3. Usa lenguaje apropiado para el nivel del estudiante ({request.context.student_grade_level})
4. {"Incluye ejemplos concretos y relacionables" if request.include_examples else ""}
5. {"Incluye 2-3 preguntas de seguimiento para mantener el diálogo" if request.include_follow_up_questions else ""}
6. Si no sabes algo, admítelo honestamente
7. Siempre termina con algo positivo o motivador
8. Idioma: {"Español chileno" if request.language == "es" else "English"}

Recuerda: Eres un apoyo, no das las respuestas directamente. Guía al estudiante a pensar.

Genera tu respuesta en formato JSON estructurado.
"""
        return prompt

# Singleton instance
content_generation_service = ContentGenerationService()