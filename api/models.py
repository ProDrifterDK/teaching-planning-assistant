from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

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

class StreamThought(BaseModel):
    type: str = "thought"
    content: str

class StreamAnswer(BaseModel):
    type: str = "answer"
    content: str

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