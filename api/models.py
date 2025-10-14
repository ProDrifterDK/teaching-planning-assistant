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
    oa_codigo_oficial: str = Field(..., description="El código oficial del OA para el cual generar el plan.")
    recurso_principal: str = Field(..., description="Recurso principal que el profesor planea usar (video, guía, etc.).")
    nivel_real_estudiantes: str = Field(..., description="Descripción del nivel de conocimiento actual de los estudiantes.")
    materiales_disponibles: Optional[str] = Field(None, description="Descripción de los materiales y recursos disponibles en la sala de clases (ej: 'Solo pizarra', 'Proyector y parlantes', etc.).")
    duracion_clase_minutos: int = Field(90, description="Duración total de la clase en minutos.")

class PlanResponse(BaseModel):
    planificacion: str

class StreamThought(BaseModel):
    type: str = "thought"
    content: str

class StreamAnswer(BaseModel):
    type: str = "answer"
    content: str