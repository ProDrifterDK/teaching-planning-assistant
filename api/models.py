from pydantic import BaseModel, Field
from typing import List, Optional

class Attitude(BaseModel):
    codigo: str
    descripcion: str

class OA(BaseModel):
    oa_codigo_oficial: str = Field(..., description="Código oficial del Objetivo de Aprendizaje.")
    descripcion_oa: str = Field(..., description="Descripción detallada del Objetivo de Aprendizaje.")
    desglose_componentes: List[str] = Field(default_factory=list, description="Lista de componentes o ejemplos del OA.")
    habilidades: List[str] = Field(default_factory=list, description="Habilidades de la Taxonomía de Bloom asociadas.")

class Eje(BaseModel):
    nombre_eje: str = Field(..., description="Nombre del eje curricular.")
    oas: List[OA] = Field(..., description="Lista de Objetivos de Aprendizaje pertenecientes a este eje.")

class AsignaturaCurso(BaseModel):
    asignatura: str
    curso: str
    actitudes: List[Attitude]
    ejes: List[Eje]

class NivelDetail(BaseModel):
    curso: str
    asignaturas: List[str]

class PlanRequest(BaseModel):
    # Contexto Curricular Esencial
    oa_codigo_oficial: str = Field(..., description="El código oficial del OA para el cual generar el plan, ej: 'LE07 OA 03'.")

    # Contexto del Aula y Pedagógico (Inputs del Profesor)
    recurso_principal: str = Field(..., description="Recurso principal que el profesor planea usar (ej: 'El cuento El gigante egoísta').")
    nivel_real_estudiantes: str = Field(..., description="Descripción del nivel de conocimiento previo de los estudiantes (ej: 'Nivel de 6° Básico en comprensión').")
    materiales_disponibles: Optional[str] = Field(None, description="Materiales específicos disponibles (ej: 'Pizarra, proyector, hojas blancas').")
    duracion_clase_minutos: int = Field(90, description="Duración total de la clase en minutos.")
    
    # Nuevos Parámetros de Contexto
    numero_estudiantes: Optional[int] = Field(None, description="Cantidad de estudiantes en el curso.")
    diversidad_aula: Optional[str] = Field(None, description="Información sobre diversidad en el aula, incluyendo estudiantes con NEE, PIE, etc.")
    clima_de_aula: Optional[str] = Field(None, description="Descripción de la dinámica y comportamiento del grupo (ej: 'Son conversadores y les gusta debatir').")
    estilo_docente_preferido: Optional[str] = Field(None, description="Enfoque metodológico preferido por el docente (ej: 'Aprendizaje Basado en Proyectos', 'Clase invertida').")
    tipo_evaluacion_formativa: Optional[str] = Field(None, description="Tipo específico de evaluación formativa deseada (ej: 'Ticket de Salida con 2 preguntas', 'Crear un mini-cómic').")
    contexto_unidad: Optional[str] = Field(None, description="Información sobre en qué parte de la unidad se encuentra la clase (ej: 'Clase de inicio de la Unidad 2 sobre el género lírico').")
    conocimientos_previos_requeridos: Optional[str] = Field(None, description="Habilidad o conocimiento prerrequisito que necesita ser reforzado (ej: 'Diferenciar entre acciones y motivaciones de personajes').")

class PlanResponse(BaseModel):
    planificacion: str

class StreamThought(BaseModel):
    type: str = "thought"
    content: str

class StreamAnswer(BaseModel):
    type: str = "answer"
    content: str