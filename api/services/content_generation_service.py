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
from api.services.schema_utils import clean_schema_for_llm
from api.services.ai_adapter import DeepSeekAIAdapter, ai_adapter
import uuid
from typing import Optional
from datetime import datetime

class ContentGenerationService:
    """Service for generating structured educational content using DeepSeek"""
    
    def __init__(self, adapter: Optional[DeepSeekAIAdapter] = None):
        self.adapter = adapter or ai_adapter

    async def _generate_json(self, prompt: str, response_model) -> dict:
        result = await self.adapter.generate_json(
            prompt,
            schema=clean_schema_for_llm(response_model.model_json_schema()),
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        )
        return result.data
    
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
        
        # Generate with DeepSeek
        lesson_data = await self._generate_json(prompt, StructuredLesson)
        
        # Add generated IDs if missing
        if 'lesson_id' not in lesson_data:
            lesson_data['lesson_id'] = f"lesson_{uuid.uuid4().hex[:8]}"
        
        return StructuredLesson(**lesson_data)
    
    async def generate_quiz(
        self,
        request: GenerateQuizRequest,
        curriculum_data: dict,
        max_retries: int = 2
    ) -> Quiz:
        """
        Generate a quiz based on curriculum OAs.
        Returns a fully structured Quiz object.
        Includes validation for duplicate questions and missing options.
        """
        prompt = self._build_quiz_prompt(request, curriculum_data)
        
        quiz_data: dict = {}
        
        for attempt in range(max_retries + 1):
            quiz_data = await self._generate_json(prompt, Quiz)
            quiz_data['quiz_id'] = f"quiz_{uuid.uuid4().hex[:8]}"
            
            # Calculate totals
            quiz_data['total_points'] = sum(q.get('points', 1) for q in quiz_data.get('questions', []))
            
            # Validate and fix quiz
            validation_result = self._validate_quiz_questions(quiz_data, request.num_questions)
            
            if validation_result['is_valid']:
                return Quiz(**quiz_data)
            
            # If not valid and we have retries left, try again with more explicit prompt
            if attempt < max_retries:
                issues = validation_result['issues']
                prompt = self._build_quiz_prompt(request, curriculum_data)
                prompt += f"\n\n## CORRECCIÓN REQUERIDA\nEl intento anterior tuvo estos problemas:\n"
                for issue in issues:
                    prompt += f"- {issue}\n"
                prompt += "\nPor favor genera preguntas que NO tengan estos problemas."
            else:
                # Last attempt - apply fixes manually
                quiz_data = self._fix_quiz_issues(quiz_data, request.num_questions)
        
        return Quiz(**quiz_data)
    
    def _validate_quiz_questions(self, quiz_data: dict, expected_count: int) -> dict:
        """Validate quiz questions for common issues"""
        issues = []
        questions = quiz_data.get('questions', [])
        
        # Check question count
        if len(questions) < expected_count:
            issues.append(f"Solo hay {len(questions)} preguntas, se esperaban {expected_count}")
        
        # Check for duplicate question texts
        question_texts = [q.get('question_text', '').lower().strip() for q in questions]
        seen_texts = set()
        duplicates = []
        for i, text in enumerate(question_texts):
            if text in seen_texts:
                duplicates.append(i + 1)
            seen_texts.add(text)
        
        if duplicates:
            issues.append(f"Preguntas duplicadas encontradas en posiciones: {duplicates}")
        
        # Check for duplicate question IDs
        question_ids = [q.get('question_id', '') for q in questions]
        if len(question_ids) != len(set(question_ids)):
            issues.append("Hay question_ids duplicados")
        
        # Check for missing options in multiple choice questions
        for i, q in enumerate(questions):
            q_type = q.get('question_type', '')
            options = q.get('options')
            correct_answer = q.get('correct_answer')
            
            if q_type == 'multiple_choice':
                if not options or len(options) < 4:
                    issues.append(f"Pregunta {i+1}: opción múltiple sin opciones completas (tiene {len(options) if options else 0})")
                elif not any(opt.get('is_correct') for opt in options):
                    issues.append(f"Pregunta {i+1}: ninguna opción marcada como correcta")
            
            if correct_answer is None:
                issues.append(f"Pregunta {i+1}: falta correct_answer")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues
        }
    
    def _fix_quiz_issues(self, quiz_data: dict, expected_count: int) -> dict:
        """Attempt to fix common quiz issues"""
        questions = quiz_data.get('questions', [])
        
        # Fix duplicate question IDs
        seen_ids = set()
        for i, q in enumerate(questions):
            original_id = q.get('question_id', '')
            if original_id in seen_ids or not original_id:
                q['question_id'] = f"Q{i+1}_{uuid.uuid4().hex[:4]}"
            seen_ids.add(q['question_id'])
        
        # Fix missing options for multiple choice
        for q in questions:
            q_type = q.get('question_type', '')
            if q_type == 'multiple_choice':
                options = q.get('options')
                if not options:
                    # Create placeholder options
                    q['options'] = [
                        {"option_id": "a", "text": "Opción A", "is_correct": True, "feedback": ""},
                        {"option_id": "b", "text": "Opción B", "is_correct": False, "feedback": ""},
                        {"option_id": "c", "text": "Opción C", "is_correct": False, "feedback": ""},
                        {"option_id": "d", "text": "Opción D", "is_correct": False, "feedback": ""}
                    ]
                    q['correct_answer'] = "a"
                elif not q.get('correct_answer'):
                    # Set correct_answer from options
                    for opt in options:
                        if opt.get('is_correct'):
                            q['correct_answer'] = opt.get('option_id')
                            break
                    if not q.get('correct_answer'):
                        q['correct_answer'] = options[0].get('option_id', 'a')
                        options[0]['is_correct'] = True
        
        quiz_data['questions'] = questions
        return quiz_data

    async def generate_activity(
        self,
        request: GenerateActivityRequest,
        curriculum_data: dict
    ) -> Activity:
        """Generate an interactive learning activity"""
        prompt = self._build_activity_prompt(request, curriculum_data)
        activity_data = await self._generate_json(prompt, Activity)
        activity_data['activity_id'] = f"act_{uuid.uuid4().hex[:8]}"
        
        return Activity(**activity_data)

    async def generate_exam(
        self,
        request: GenerateExamRequest,
        curriculum_data: dict
    ) -> Exam:
        """Generate a summative exam"""
        prompt = self._build_exam_prompt(request, curriculum_data)
        exam_data = await self._generate_json(prompt, Exam)
        exam_data['exam_id'] = f"exam_{uuid.uuid4().hex[:8]}"
        
        return Exam(**exam_data)

    async def generate_reinforcement(
        self,
        request: GenerateReinforcementRequest,
        curriculum_data: dict
    ) -> ReinforcementPlan:
        """Generate reinforcement materials for struggling students"""
        prompt = self._build_reinforcement_prompt(request, curriculum_data)
        plan_data = await self._generate_json(prompt, ReinforcementPlan)
        plan_data['plan_id'] = f"reinf_{uuid.uuid4().hex[:8]}"
        
        return ReinforcementPlan(**plan_data)

    async def generate_summary(
        self,
        request: GenerateSummaryRequest,
        curriculum_data: dict
    ) -> UnitSummary:
        """Generate a unit summary with optional flashcards and concept maps"""
        prompt = self._build_summary_prompt(request, curriculum_data)
        summary_data = await self._generate_json(prompt, UnitSummary)
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
        tutor_data = await self._generate_json(prompt, TutorResponse)
        return TutorResponse(**tutor_data)

    async def adapt_content_for_nee(
        self,
        request: AdaptContentRequest
    ) -> AdaptedContent:
        """
        Adapt educational content for students with special educational needs.
        Returns fully structured AdaptedContent with all modifications and guidance.
        """
        prompt = self._build_adaptation_prompt(request)
        adapted_data = await self._generate_json(prompt, AdaptedContent)
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
        result_data = await self._generate_json(prompt, ValidationResult)
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

## IMPORTANTE: REQUISITOS CRÍTICOS
1. **CADA PREGUNTA DEBE SER ÚNICA Y DIFERENTE** - NO repitas la misma pregunta. Cada pregunta debe evaluar un aspecto diferente del OA.
2. **TODAS las preguntas de selección múltiple DEBEN tener el campo `options` con 4 opciones** - NUNCA dejar `options` como null.
3. **TODAS las preguntas DEBEN tener `correct_answer` definido** - NUNCA dejar `correct_answer` como null.
4. **Cada `question_id` debe ser ÚNICO** - Usa formato "{request.subject[:4].upper()}{request.grade_level}B_001_Q1", "_Q2", "_Q3", etc.

## Contexto del Currículum
Asignatura: {request.subject}
Nivel: {request.grade_level}

## Objetivos de Aprendizaje (OAs) a evaluar:
{oas_text}

## Requisitos del Quiz
- Número de preguntas: {request.num_questions} (TODAS deben ser DIFERENTES entre sí)
- {question_types_text}
- {difficulty_text}
- Idioma: {"Español" if request.language == "es" else "English"}
{f"- Niveles de Bloom objetivo: {[bl.value for bl in request.bloom_levels]}" if request.bloom_levels else ""}
{f"- Límite de tiempo: {request.time_limit_minutes} minutos" if request.time_limit_minutes else ""}
{f"- Contexto adicional: {request.context}" if request.context else ""}

## Instrucciones OBLIGATORIAS
1. Genera EXACTAMENTE {request.num_questions} preguntas DIFERENTES - cada una sobre un aspecto distinto del tema
2. Cada pregunta debe evaluar un OA específico desde un ángulo diferente
3. Incluye variedad en tipos de preguntas si es permitido
4. **Para preguntas de selección múltiple (multiple_choice):**
   - El campo `options` DEBE ser un array con 4 objetos
   - Cada opción DEBE tener: option_id ("a", "b", "c", "d"), text (el texto de la opción), is_correct (true/false), feedback (opcional)
   - EXACTAMENTE UNA opción debe tener is_correct: true
   - El campo `correct_answer` DEBE ser el option_id de la respuesta correcta ("a", "b", "c", o "d")
5. **Para preguntas de verdadero/falso:**
   - El campo `correct_answer` DEBE ser "true" o "false"
6. **Para preguntas de respuesta corta o completar:**
   - El campo `correct_answer` DEBE contener la respuesta esperada como texto
7. {"Incluye pistas para cada pregunta" if request.include_hints else "No incluir pistas"}
8. {"Incluye explicación de la respuesta correcta" if request.include_explanations else "No incluir explicaciones"}
9. Asegura que las preguntas sean claras y sin ambigüedad
10. Las respuestas incorrectas deben ser plausibles pero claramente incorrectas

## Ejemplo de Pregunta de Selección Múltiple Correcta:
```json
{{
  "question_id": "LENG1B_001_Q1",
  "question_type": "multiple_choice",
  "question_text": "Observa la imagen de un SOL. ¿Cuál de estas palabras dice 'sol'?",
  "difficulty": "easy",
  "points": 2,
  "linked_oa": "LENG1 OA 01",
  "bloom_level": "remember",
  "options": [
    {{"option_id": "a", "text": "sol", "is_correct": true, "feedback": "¡Correcto! La palabra 'sol' tiene las letras s-o-l."}},
    {{"option_id": "b", "text": "sal", "is_correct": false, "feedback": "Esta palabra dice 'sal', no 'sol'."}},
    {{"option_id": "c", "text": "sil", "is_correct": false, "feedback": "Esta palabra dice 'sil', no 'sol'."}},
    {{"option_id": "d", "text": "sul", "is_correct": false, "feedback": "Esta palabra dice 'sul', no 'sol'."}}
  ],
  "correct_answer": "a",
  "explanation": "La palabra 'sol' se escribe con las letras s-o-l y representa nuestra estrella."
}}
```

## VALIDACIÓN FINAL
Antes de generar, verifica:
- [ ] ¿Tengo {request.num_questions} preguntas DIFERENTES?
- [ ] ¿Cada question_id es único (_Q1, _Q2, _Q3...)?
- [ ] ¿Cada pregunta multiple_choice tiene options con 4 elementos?
- [ ] ¿Cada pregunta tiene correct_answer definido (no null)?
- [ ] ¿Las preguntas cubren diferentes aspectos del tema?

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
Eres un experto pedagogo chileno especializado en educación digital. Genera una planificación de clase estructurada siguiendo el currículum nacional de Chile.

## IMPORTANTE: CONTEXTO DE APRENDIZAJE DIGITAL
Esta planificación es para una **PLATAFORMA DE APRENDIZAJE DIGITAL/ONLINE**. NO diseñes actividades presenciales con materiales físicos.

### Tipos de Actividades PERMITIDAS (digitales):
- Videos interactivos con preguntas integradas
- Actividades de arrastrar y soltar (drag-and-drop) digitales
- Ejercicios con imágenes clicables
- Guías de pronunciación con audio integrado
- Texto interactivo (clic para expandir, resaltar, etc.)
- Flashcards digitales con animaciones
- Elementos de gamificación (puntos, badges, progreso)
- Foros de discusión y prompts de reflexión
- Manipulativos virtuales (fichas de letras digitales, bloques numéricos virtuales, etc.)
- Quizzes interactivos con retroalimentación inmediata
- Actividades de completar oraciones con campos de texto
- Ejercicios de selección múltiple con imágenes
- Actividades de ordenar secuencias arrastrando elementos
- Grabación de voz para práctica de pronunciación

### Tipos de Actividades PROHIBIDAS (requieren presencialidad):
- Uso de materiales físicos (cajas, tarjetas de cartón, objetos reales)
- Actividades que requieren manipulación de objetos físicos
- Trabajos en cuadernos o hojas de papel
- Uso de letras móviles físicas o magnéticas
- Actividades de recortar y pegar
- Cualquier actividad que no pueda realizarse 100% en pantalla

## Contexto del Currículum
Asignatura: {request.subject}
Nivel: {request.grade_level}

## Objetivos de Aprendizaje (OAs) a cubrir:
{oas_text}

## Requisitos de la Clase
- Duración total: {request.duration_minutes} minutos
- Idioma: {"Español" if request.language == "es" else "English"}
- Modalidad: 100% DIGITAL/ONLINE
{f"- Contexto adicional: {request.context}" if request.context else ""}

## Instrucciones
1. Diseña una clase completa con inicio, desarrollo y cierre - TODO DEBE SER DIGITAL
2. Incluye actividades específicas que funcionen en pantalla (videos, drag-and-drop, quizzes interactivos)
3. Define objetivos medibles con criterios de éxito
4. Especifica qué tipo de componente digital se usaría para cada actividad (ej: "Video interactivo", "Drag-and-drop de letras", "Quiz de selección múltiple con imágenes")
5. {"Incluye notas de diferenciación para distintos ritmos de aprendizaje" if request.include_differentiation else ""}
6. {"Incluye rúbrica de evaluación" if request.include_assessment_rubric else ""}

## Ejemplos de Actividades Digitales por Asignatura:

### Lenguaje:
- "Arrastra las letras virtuales para formar la palabra que ves en la imagen"
- "Escucha el audio y selecciona la imagen correcta"
- "Completa la palabra escribiendo las letras que faltan"
- "Mira el video del cuento y responde las preguntas que aparecen"

### Matemáticas:
- "Arrastra los bloques numéricos virtuales para mostrar la cantidad"
- "Selecciona el resultado correcto de la operación"
- "Ordena los números de menor a mayor arrastrándolos"
- "Completa la secuencia numérica"

### Ciencias:
- "Mira el video del experimento y predice qué sucederá"
- "Arrastra las etiquetas a las partes correctas del diagrama"
- "Ordena los pasos del ciclo de vida"

Genera la planificación en formato JSON estructurado. RECUERDA: Todas las actividades deben ser 100% digitales.
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