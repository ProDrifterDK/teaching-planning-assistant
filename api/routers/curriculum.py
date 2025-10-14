from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from typing import Annotated
from ..services.curriculum_service import CurriculumService, get_curriculum_service
from ..models import Eje, User
from .auth import get_current_active_user

router = APIRouter(
    prefix="/curriculum",
    tags=["Motor Curricular"]
)

@router.get("/niveles", response_model=Dict[str, List[str]])
def get_niveles(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Obtiene una estructura anidada de todos los cursos y sus asignaturas.
    Ideal para poblar menús desplegables en el frontend.
    """
    return service.get_niveles()

@router.get("/oas", response_model=List[Eje])
def get_oas(
    curso: str,
    asignatura: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Obtiene la lista completa de ejes y sus Objetivos de Aprendizaje (OAs)
    para un curso y asignatura específicos.
    """
    ejes = service.get_oas_by_curso_asignatura(curso, asignatura)
    if not ejes:
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontraron datos para el curso '{curso}' y la asignatura '{asignatura}'."
        )
    return ejes