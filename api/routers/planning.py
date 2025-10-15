from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from google.genai import types
import google.genai as genai
import logging
import json
from sqlalchemy.orm import Session

from ..models import PlanRequest, StreamThought, StreamAnswer, User
from ..core.config import settings
from ..core.pricing import calculate_cost
from ..services.curriculum_service import CurriculumService, get_curriculum_service
from .auth import get_current_active_user
from ..db.session import get_db
from ..db import planning_crud

router = APIRouter(
    prefix="/planning",
    tags=["Co-piloto de Planificación"]
)

async def stream_generator(prompt: str, oa_codigo: str, user_id: int, db: Session):
    """
    Generador asíncrono que produce fragmentos de la respuesta de Gemini.
    Al finalizar, calcula el costo y lo registra en la base de datos.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    full_config = types.GenerateContentConfig(
        max_output_tokens=65536,
        thinking_config=types.ThinkingConfig(
            thinking_budget=-1,
            include_thoughts=True
        )
    )
    final_usage_metadata = None

    try:
        stream = await client.aio.models.generate_content_stream(
            model='gemini-2.5-pro',
            contents=prompt,
            config=full_config
        )

        async for chunk in stream:
            if chunk.usage_metadata:
                final_usage_metadata = chunk.usage_metadata

            if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if not part.text:
                        continue
                    if hasattr(part, 'thought') and part.thought:
                        thought_chunk = StreamThought(content=part.text)
                        yield f"data: {thought_chunk.json()}\n\n"
                    else:
                        answer_chunk = StreamAnswer(content=part.text)
                        yield f"data: {answer_chunk.json()}\n\n"

    except Exception as e:
        logging.error(f"Error durante el stream para OA '{oa_codigo}': {e}")
        error_response = {"type": "error", "content": str(e)}
        yield f"data: {json.dumps(error_response)}\n\n"
    finally:
        if final_usage_metadata:
            input_tokens = final_usage_metadata.prompt_token_count or 0
            output_tokens = final_usage_metadata.candidates_token_count or 0
            thought_tokens = final_usage_metadata.thoughts_token_count or 0
            cost = calculate_cost(input_tokens, output_tokens + thought_tokens)
            
            # Guardar el log en la base de datos
            try:
                planning_crud.create_planning_log(
                    db=db,
                    user_id=user_id,
                    oa_codigo=oa_codigo,
                    cost=cost,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    thought_tokens=thought_tokens,
                )
                logging.info(f"Costo de ${cost:.6f} registrado para el usuario ID {user_id} y OA '{oa_codigo}'.")
            except Exception as e:
                logging.error(f"Error al registrar el costo para el usuario ID {user_id}: {e}")

@router.post(
    "/generate-plan",
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": """Respuesta en formato Server-Sent Events (SSE). Cada evento es una línea `data:` seguida de un objeto JSON.
            
Ejemplo de evento de 'pensamiento':
`data: {"type": "thought", "content": "Estoy analizando el OA..."}`

Ejemplo de evento de 'respuesta':
`data: {"type": "answer", "content": "Aquí está la primera parte..."}`
""",
        }
    },
)
async def generate_plan(
    request: PlanRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: CurriculumService = Depends(get_curriculum_service),
    db: Session = Depends(get_db)
):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="La API de Gemini no está configurada.")

    oa_details = service.find_oa_details(request.oa_codigo_oficial)
    if not oa_details:
        raise HTTPException(status_code=404, detail=f"OA '{request.oa_codigo_oficial}' no encontrado.")
    
    oa_completo = oa_details["oa_completo"]
    contexto_asignatura = oa_details["contexto_asignatura"]
    eje = oa_details["eje"]
    
    # --- Construcción Dinámica del Prompt ---
    prompt_parts = [
        "Rol: Actúa como un experto en diseño instruccional y un co-piloto para un profesor chileno. Tu objetivo es crear una planificación de clase realista, útil y lista para ser usada. La planificación debe estar alineada con el currículum nacional chileno y adaptada al contexto específico del aula y las necesidades del docente. La planificación debe ser escrita con lujo de detalles, sin omitir pasos, y debe ser práctica y aplicable en un entorno real de aula.",
        "---",
        "Contexto Curricular:",
        f"- Asignatura: {contexto_asignatura.get('asignatura', 'N/A')}",
        f"- Curso: {contexto_asignatura.get('curso', 'N/A')}",
        f"- Eje Curricular: {eje.get('nombre_eje', 'N/A')}",
        "- Objetivo de Aprendizaje (OA) a tratar:",
        f"  - Código: {oa_completo.get('oa_codigo_oficial', 'N/A')}",
        f"  - Descripción: {oa_completo.get('descripcion_oa', 'N/A')}",
        f"  - Componentes Clave: {', '.join(oa_completo.get('desglose_componentes', []))}",
        f"  - Habilidades de Bloom: {', '.join(oa_completo.get('habilidades', []))}",
        f"- Actitudes a Fomentar: {[act.get('descripcion', '') for act in contexto_asignatura.get('actitudes', [])]}",
        "---",
        "Contexto del Aula:",
        f"- Duración de la Clase: {request.duracion_clase_minutos} minutos."
    ]
    if request.numero_estudiantes:
        prompt_parts.append(f"- Número de Estudiantes: {request.numero_estudiantes}")
    if request.clima_de_aula:
        prompt_parts.append(f"- Clima y Dinámica del Grupo: {request.clima_de_aula}")
    if request.diversidad_aula:
        prompt_parts.append(f"- Diversidad en el Aula: {request.diversidad_aula}")
    if request.materiales_disponibles:
        prompt_parts.append(f"- Materiales Disponibles: {request.materiales_disponibles}. Adapta las actividades estrictamente a estos materiales.")

    prompt_parts.extend([
        "---",
        "Contexto Pedagógico:",
        f"- Recurso Principal: {request.recurso_principal}",
        f"- Nivel Real de los Estudiantes: {request.nivel_real_estudiantes}"
    ])
    if request.conocimientos_previos_requeridos:
        prompt_parts.append(f"- Conocimientos Previos a Reforzar: {request.conocimientos_previos_requeridos}")
    if request.estilo_docente_preferido:
        prompt_parts.append(f"- Estilo Docente Preferido: {request.estilo_docente_preferido}")
    if request.tipo_evaluacion_formativa:
        prompt_parts.append(f"- Tipo de Evaluación Formativa Deseada: {request.tipo_evaluacion_formativa}")
    if request.contexto_unidad:
        prompt_parts.append(f"- Momento de la Unidad: {request.contexto_unidad}")
    if request.solicitud_especial:
        prompt_parts.append(f"- Solicitud Especial del Docente: {request.solicitud_especial}")
        
    prompt_parts.extend([
        "---",
        "Instrucciones de Salida:",
        "Genera una planificación de clase en formato Markdown. La planificación debe ser completa, realista y estar estructurada en tres fases claras: Inicio, Desarrollo y Cierre.",
        "Ajusta la duración de cada fase según la duración total de la clase.",
        "Considera todas las restricciones y contextos proporcionados para crear actividades y evaluaciones coherentes y aplicables.",
        "Si se mencionó diversidad, sugiere adaptaciones específicas (ej. 'Para los estudiantes con TEA...').",
        "Si se pidió reforzar conocimientos previos, diseña una actividad de Inicio explícita para ello.",
        "Si se pidió un tipo de evaluación, detalla esa actividad en el Cierre."
    ])

    prompt = "\n".join(prompt_parts)

    return StreamingResponse(
        stream_generator(
            prompt=prompt,
            oa_codigo=request.oa_codigo_oficial,
            user_id=current_user.id,
            db=db
        ),
        media_type="text/event-stream"
    )