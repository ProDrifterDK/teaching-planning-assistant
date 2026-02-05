PATHWAY_GENERATION_PROMPT = """
Eres un experto en diseño instruccional y gamificación educativa para el currículum chileno.
Genera un Pathway (Misión) de aprendizaje completo y estructurado.

## Contexto Curricular
Asignatura: {subject}
Nivel: {grade_level}° Básico/Medio
Unidad: {unit_name}

## Objetivos de Aprendizaje (OAs) a cubrir:
{oa_descriptions}

## Configuración de la Misión
- Tema narrativo: {mission_theme}
- Estilo de gancho: {hook_style}
- Duración total estimada: {estimated_total_minutes} minutos
- Número de capítulos: {chapters_count}
- Incluir checkpoints: {include_checkpoints}
- Incluir side quests: {include_side_quests}
{class_profile_text}

## Estructura Requerida

### Para cada Capítulo:
1. **Hook/Gancho** (5-8 min): Situación problema o historia que engancha
2. **Lección** (10-15 min): Contenido principal con ejemplos claros
3. **Actividad** (10-15 min): Práctica interactiva 
4. **Quiz de verificación** (5-8 min): Evaluación formativa

### Elementos de Gamificación:
- Metáfora de misión coherente con el tema {mission_theme}
- Puntos XP por cada nodo completado
- Side quests opcionales para enriquecimiento
- Badge al completar la misión
- Narrativa que conecta todos los capítulos

### Para cada Nodo incluye:
- content_generation_prompt: Instrucciones detalladas para generar el contenido
- objectives: Objetivos específicos del nodo
- estimated_minutes: Duración estimada
- on_complete: Configuración de qué sigue al completar
- on_fail: Qué hacer si el estudiante no supera (para checkpoints)

## Requisitos de Diferenciación
{differentiation_text}

## Formato de Respuesta
Genera un JSON estructurado con:
- title: Título atractivo de la misión
- description: Descripción breve y motivadora
- mission_metaphor: Nombre, icono y narrativa del tema
- chapters: Array de capítulos con sus nodos
- total_nodes: Conteo total de nodos
- total_checkpoints: Conteo de checkpoints
- estimated_total_minutes: Duración total
- rewards: XP, badge sugerido, elegibilidad para certificado
- suggested_prerequisites: OAs previos recomendados

IMPORTANTE: 
- Los IDs de nodos deben seguir el formato: ch_{{chapter_order:02d}}_node_{{node_order:03d}}
- Cada nodo debe tener on_complete.default_next_node_id apuntando al siguiente
- Los checkpoints deben tener conditional_next para rutas de remediación
- El contenido debe ser apropiado para estudiantes chilenos de {grade_level}° nivel
"""

QUIZ_GENERATION_PROMPT = """
Eres un experto en evaluación educativa chilena. Genera un quiz interactivo con múltiples tipos de preguntas.

## Contexto
Asignatura: {subject}
Nivel: {curso}
Tipo de quiz: {quiz_type}
{topic_text}

## OAs a evaluar:
{oa_descriptions}

## Configuración del Quiz
- Número de preguntas: {num_questions}
- Límite de tiempo: {time_limit_text}
- Distribución de dificultad: {difficulty_distribution}
- Nivel de feedback: {feedback_level}

## Distribución de Tipos de Preguntas
{question_types_distribution}

## TIPOS DE PREGUNTAS DISPONIBLES Y SU FORMATO

### 1. multiple_choice (Selección Única)
```json
{{
  "type": "multiple_choice",
  "stem": "¿Pregunta clara?",
  "options": [
    {{"id": "a", "text": "Opción A", "is_correct": true, "feedback": "¡Correcto porque..."}},
    {{"id": "b", "text": "Opción B", "is_correct": false, "feedback": "Incorrecto porque..."}},
    {{"id": "c", "text": "Opción C", "is_correct": false, "feedback": "..."}},
    {{"id": "d", "text": "Opción D", "is_correct": false, "feedback": "..."}}
  ],
  "correct_answer": {{"type": "exact", "value": "a"}}
}}
```

### 2. multiple_select (Selección Múltiple)
```json
{{
  "type": "multiple_select",
  "stem": "Selecciona TODAS las opciones correctas:",
  "options": [
    {{"id": "a", "text": "Opción correcta 1", "is_correct": true}},
    {{"id": "b", "text": "Opción incorrecta", "is_correct": false}},
    {{"id": "c", "text": "Opción correcta 2", "is_correct": true}},
    {{"id": "d", "text": "Opción incorrecta", "is_correct": false}}
  ],
  "correct_answer": {{"type": "exact", "value": ["a", "c"]}}
}}
```

### 3. true_false (Verdadero/Falso)
```json
{{
  "type": "true_false",
  "stem": "Afirmación a evaluar",
  "options": [
    {{"id": "true", "text": "Verdadero", "is_correct": true}},
    {{"id": "false", "text": "Falso", "is_correct": false}}
  ],
  "correct_answer": {{"type": "exact", "value": "true"}}
}}
```

### 4. matching (Asociar Pares)
```json
{{
  "type": "matching",
  "stem": "Une cada elemento de la izquierda con su correspondiente:",
  "matching_pairs": [
    {{"left_id": "l1", "left_text": "Concepto 1", "right_id": "r1", "right_text": "Definición 1"}},
    {{"left_id": "l2", "left_text": "Concepto 2", "right_id": "r2", "right_text": "Definición 2"}},
    {{"left_id": "l3", "left_text": "Concepto 3", "right_id": "r3", "right_text": "Definición 3"}}
  ],
  "correct_answer": {{"type": "exact", "value": {{"l1": "r1", "l2": "r2", "l3": "r3"}}}}
}}
```

### 5. ordering (Ordenar Secuencia)
```json
{{
  "type": "ordering",
  "stem": "Ordena los siguientes pasos correctamente:",
  "ordering_items": [
    {{"id": "step1", "text": "Primer paso"}},
    {{"id": "step2", "text": "Segundo paso"}},
    {{"id": "step3", "text": "Tercer paso"}},
    {{"id": "step4", "text": "Cuarto paso"}}
  ],
  "correct_answer": {{"type": "exact", "value": ["step1", "step2", "step3", "step4"]}}
}}
```

### 6. fill_in_blank (Completar Espacios)
```json
{{
  "type": "fill_in_blank",
  "stem": "Completa: La capital de Chile es ___.",
  "blanks": [
    {{"id": "b1", "correct_answers": ["Santiago", "santiago"], "position": 0}}
  ],
  "correct_answer": {{"type": "contains", "value": ["Santiago"]}}
}}
```

### 7. short_answer (Respuesta Corta)
```json
{{
  "type": "short_answer",
  "stem": "¿Qué es...? Explica brevemente.",
  "correct_answer": {{"type": "contains", "value": ["palabra_clave1", "palabra_clave2"]}}
}}
```

### 8. drag_drop (Arrastrar y Soltar)
```json
{{
  "type": "drag_drop",
  "stem": "Arrastra cada elemento a su categoría correcta:",
  "drag_drop_config": {{
    "items": [
      {{"id": "item1", "label": "Elemento 1"}},
      {{"id": "item2", "label": "Elemento 2"}},
      {{"id": "item3", "label": "Elemento 3"}}
    ],
    "zones": [
      {{"id": "zone1", "label": "Categoría A", "correct_item_ids": ["item1"]}},
      {{"id": "zone2", "label": "Categoría B", "correct_item_ids": ["item2", "item3"]}}
    ],
    "allow_multiple_in_zone": true,
    "click_to_select_enabled": true
  }},
  "correct_answer": {{"type": "exact", "value": {{"item1": "zone1", "item2": "zone2", "item3": "zone2"}}}}
}}
```

## Requisitos para CADA Pregunta

### Campos Obligatorios:
- id: Formato "q_{{order:03d}}" (q_001, q_002, etc.)
- type: Uno de los 8 tipos
- order: Número de orden
- stem: Enunciado claro y sin ambigüedad
- correct_answer: Con type y value apropiados
- points: Puntos (default 10)
- difficulty: "easy", "medium", o "hard"
- skill: Habilidad evaluada
- oa_code: Código del OA relacionado
- feedback: Con correct e incorrect explicativos

### Campos de Confianza (si include_confidence_tracking):
- confidence_enabled: true
- confidence_scoring: Puntos por nivel de confianza

### Campos de Accesibilidad:
- accessibility.read_aloud_text: Versión para lectura en voz alta
- accessibility.simplified_version: Versión simplificada (si aplica)

### Campos de Hints (si include_hints):
- hints: Array de pistas progresivas

## Adaptaciones NEE
{nee_adaptations_text}

## Requisitos del Quiz
1. TODAS las preguntas deben ser ÚNICAS y evaluar diferentes aspectos
2. Los question_id deben ser únicos y seguir el formato q_001, q_002, etc.
3. El feedback debe ser educativo, no solo decir "correcto/incorrecto"
4. Las opciones incorrectas deben ser plausibles (distractores de calidad)
5. Incluir variedad en los tipos de preguntas según la distribución dada
6. El lenguaje debe ser apropiado para estudiantes de {curso}

## Formato de Salida
```json
{{
  "id": "quiz_{{uuid}}",
  "title": "Título descriptivo del quiz",
  "type": "{quiz_type}",
  "oa_codes": [...],
  "time_limit": {time_limit_value},
  "total_points": suma_de_puntos,
  "passing_score": 70,
  "instructions": "Instrucciones claras para el estudiante",
  "confidence_instructions": "Instrucciones sobre niveles de confianza",
  "questions": [...],
  "nee_adaptations": {{...}}
}}
```
"""

MISCONCEPTION_ANALYSIS_PROMPT = """
Eres un experto en diagnóstico pedagógico y detección de errores conceptuales.
Analiza las respuestas incorrectas del estudiante para identificar misconceptions.

## Información del Estudiante
ID: {student_id}
Nivel: {grade_level}°
Asignatura: {subject}
Tema: {topic}
{nee_profile_text}

## Respuestas Incorrectas a Analizar
{wrong_answers_json}

## Tu Tarea

### 1. Identificar Misconceptions
Para cada respuesta incorrecta, analiza:
- ¿Qué concepto específico está mal entendido?
- ¿Es un error procedimental o conceptual?
- ¿Hay un patrón común entre las respuestas?
- ¿Cuál es la lógica detrás del error del estudiante?

### 2. Categorizar Misconceptions
Categorías posibles:
- conceptual_error: Error en comprensión del concepto
- procedural_error: Error en la aplicación del procedimiento
- careless_mistake: Error por descuido (no indica misconception)
- reading_comprehension: Error por no entender la pregunta
- prerequisite_gap: Falta de conocimiento previo necesario

### 3. Evaluar Severidad
- low: Error menor, fácil de corregir
- medium: Error significativo pero común
- high: Error que indica brecha importante
- critical: Error que bloquea avance a contenido posterior

### 4. Generar Remediation
Para cada misconception, sugiere:
- Tipo de remediation apropiado
- Contenido específico a revisar
- Actividades para corregir el error
- Tiempo estimado de remediation

### 5. Determinar si Alertar al Profesor
Criterios para alerta:
- Misconception persistente (aparece múltiples veces)
- Severidad alta o crítica
- Confianza alta con respuesta incorrecta
- Patrón que indica problema más profundo

## Formato de Respuesta
```json
{{
  "quiz_id": "{quiz_id}",
  "student_id": "{student_id}",
  "analysis_timestamp": "ISO timestamp",
  "total_wrong_answers": número,
  "misconceptions_detected": [
    {{
      "id": "misconception_{{topic_abbr}}_{{number:03d}}",
      "name": "Nombre corto del misconception",
      "description": "Descripción detallada",
      "affected_question_ids": ["q_001", ...],
      "confidence_score": 0.0-1.0,
      "severity": "low|medium|high|critical",
      "is_persistent": false,
      "category": "tipo_de_error"
    }}
  ],
  "remediation_suggestions": [
    {{
      "misconception_id": "id del misconception",
      "suggestion_type": "tipo de remediación",
      "title": "Título de la sugerencia",
      "description": "Descripción detallada",
      "estimated_time_minutes": número,
      "priority": "immediate|soon|when_available",
      "content_reference": "referencia a contenido existente si aplica",
      "generated_content": {{contenido generado si es necesario}}
    }}
  ],
  "teacher_alert": {{
    "alert_level": "info|warning|urgent",
    "student_id": "{student_id}",
    "summary": "Resumen para el profesor",
    "detailed_analysis": "Análisis detallado",
    "recommended_actions": ["acción 1", "acción 2"],
    "related_misconceptions": ["id1", "id2"],
    "requires_acknowledgment": true/false
  }},
  "overall_understanding_score": 0.0-1.0,
  "knowledge_gaps": ["brecha 1", "brecha 2"],
  "strengths_identified": ["fortaleza 1", "fortaleza 2"],
  "next_steps": ["paso 1", "paso 2", "paso 3"]
}}
```

## Consideraciones Especiales
{special_considerations}

## Idioma de Respuesta
Genera todo el contenido en {language}.
"""

ADAPTIVE_RECOMMENDATION_PROMPT = """
Eres un sistema de recomendación adaptativa para aprendizaje personalizado.
Genera recomendaciones de contenido para el estudiante basándote en su progreso.

## Perfil del Estudiante
ID: {student_id}
Datos de progreso:
{student_progress_json}

## Contexto de Solicitud
Tipo de contexto: {context_type}
Pathway actual: {current_pathway_id}
Límite de recomendaciones: {limit}

## Datos Disponibles
{available_content_json}

## Algoritmo de Priorización

### Pesos Base por Razón:
- overdue_assignment: 100 (máxima prioridad)
- review_due (spaced repetition): 80
- pathway_next: 70
- upcoming_assignment: 60
- weak_area: 50
- interest_match: 40
- exploration: 30

### Modificadores:
- +10 por cada día de atraso (max +30)
- +20 si hay misconception detectado en ese tema
- +15 si es contenido de prerequisito faltante
- +10 bonus de recencia para pathway activo

## Genera

### 1. Lista de Recomendaciones
Para cada recomendación incluye:
- content_id y content_type
- Razón de la recomendación
- Prioridad calculada (0-100)
- Urgencia y contexto

### 2. Insights del Estudiante
- Nivel de dominio actual
- Tendencia reciente
- Áreas de foco sugeridas
- Alertas si hay patrones preocupantes

### 3. Estadísticas de Aprendizaje
- Tiempo total esta semana
- Contenido completado
- Puntaje promedio
- Días de racha

## Formato de Salida
JSON estructurado con recommendations, insights y metadata.
"""
