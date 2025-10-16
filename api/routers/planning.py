from typing import Annotated, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from google.genai import types
import google.genai as genai
import logging
import json
import time
from sqlalchemy.orm import Session
from io import BytesIO

from ..models import PlanRequest, StreamThought, StreamAnswer, User, PlanningLogResponse, PlanningLogDetailResponse, MultimodalResources, AttachmentDetail
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

async def stream_generator(contents: List[Any], request_data: PlanRequest, user_id: int, db: Session):
    """
    Generador asíncrono que produce fragmentos de la respuesta de Gemini a partir de un prompt multimodal.
    Al finalizar, acumula la respuesta, calcula el costo y lo registra todo en la base de datos.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    full_markdown_response = ""
    
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
            contents=contents,
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
                        full_markdown_response += part.text
                        answer_chunk = StreamAnswer(content=part.text)
                        yield f"data: {answer_chunk.json()}\n\n"

    except Exception as e:
        logging.error(f"Error durante el stream para OA '{request_data.oa_codigo_oficial}': {e}")
        error_response = {"type": "error", "content": str(e)}
        yield f"data: {json.dumps(error_response)}\n\n"
    finally:
        if final_usage_metadata and full_markdown_response:
            input_tokens = final_usage_metadata.prompt_token_count or 0
            output_tokens = final_usage_metadata.candidates_token_count or 0
            thought_tokens = final_usage_metadata.thoughts_token_count or 0
            cost = calculate_cost(input_tokens, output_tokens + thought_tokens)
            
            try:
                planning_crud.create_planning_log(
                    db=db,
                    user_id=user_id,
                    oa_codigo=request_data.oa_codigo_oficial,
                    cost=cost,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    thought_tokens=thought_tokens,
                    plan_request_data=request_data.model_dump(),
                    plan_markdown=full_markdown_response,
                )
                logging.info(f"Planificación y costo de ${cost:.6f} registrados para el usuario ID {user_id} y OA '{request_data.oa_codigo_oficial}'.")
            except Exception as e:
                logging.error(f"Error al registrar la planificación para el usuario ID {user_id}: {e}")

@router.post(
    "/generate-plan",
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Respuesta en formato Server-Sent Events (SSE).",
        }
    },
)
async def generate_plan(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: CurriculumService = Depends(get_curriculum_service),
    db: Session = Depends(get_db),
    
    oa_codigo_oficial: Annotated[str, Form()] = "",
    curso: Annotated[str, Form()] = "", # Nuevo parámetro para desambiguación
    recurso_principal: Annotated[str, Form()] = "",
    nivel_real_estudiantes: Annotated[str, Form()] = "",
    duracion_clase_minutos: Annotated[int, Form()] = 90,
    materiales_disponibles: Annotated[Optional[str], Form()] = None,
    numero_estudiantes: Annotated[Optional[int], Form()] = None,
    diversidad_aula: Annotated[Optional[str], Form()] = None,
    clima_de_aula: Annotated[Optional[str], Form()] = None,
    estilo_docente_preferido: Annotated[Optional[str], Form()] = None,
    tipo_evaluacion_formativa: Annotated[Optional[str], Form()] = None,
    contexto_unidad: Annotated[Optional[str], Form()] = None,
    conocimientos_previos_requeridos: Annotated[Optional[str], Form()] = None,
    solicitud_especial: Annotated[Optional[str], Form()] = None,
    
    youtube_url: Annotated[Optional[str], Form()] = None,
    attachments: Annotated[Optional[List[UploadFile]], File()] = None
):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="La API de Gemini no está configurada.")
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    form_data = {
        field: value for field, value in locals().items() 
        if field in PlanRequest.model_fields and field not in ['current_user', 'service', 'db']
    }
    request = PlanRequest(**form_data)
    
    oa_details = service.find_oa_details(request.oa_codigo_oficial, curso=request.curso)
    if not oa_details:
        raise HTTPException(status_code=404, detail=f"OA '{request.oa_codigo_oficial}' no encontrado para el curso '{request.curso}'.")
    
    oa_completo = oa_details["oa_completo"]
    contexto_asignatura = oa_details["contexto_asignatura"]
    eje = oa_details["eje"]
    
    # --- Logging Detallado de la Solicitud ---
    log_details = {
        "user": current_user.username,
        "request": {
            "oa_codigo_oficial": request.oa_codigo_oficial,
            "recurso_principal": request.recurso_principal,
            "has_youtube_url": bool(youtube_url),
            "attachment_count": len(attachments) if attachments else 0,
        },
        "context": {
            "asignatura": contexto_asignatura.get('asignatura', 'N/A'),
            "curso": contexto_asignatura.get('curso', 'N/A'),
            "oa_descripcion": oa_completo.get('descripcion_oa', 'N/A'),
        }
    }
    logging.info(f"Generando plan con los siguientes detalles: {json.dumps(log_details, indent=2)}")

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
    
    prompt_text = "\n".join(prompt_parts)
    contents: List[Any] = [prompt_text]
    
    processed_attachments = []
    processed_youtube_urls = []

    if attachments:
        for upload_file in attachments:
            try:
                logging.info(f"Subiendo archivo: {upload_file.filename}")
                file_bytes = await upload_file.read()
                bytes_io_file = BytesIO(file_bytes)
                
                uploaded_file: Any = client.files.upload(file=bytes_io_file)
                assert uploaded_file is not None

                while uploaded_file.state.name == "PROCESSING":
                    logging.info(f"Archivo {uploaded_file.name} en procesamiento, esperando 5 segundos...")
                    time.sleep(5)
                    uploaded_file = client.files.get(name=uploaded_file.name)
                    assert uploaded_file is not None
                
                if uploaded_file.state.name != "ACTIVE":
                    raise HTTPException(status_code=500, detail=f"No se pudo procesar el archivo: {upload_file.filename}")

                contents.append(uploaded_file)
                if upload_file.filename:
                    processed_attachments.append(AttachmentDetail(filename=upload_file.filename, gemini_uri=uploaded_file.uri))
                logging.info(f"Archivo {uploaded_file.name} listo y añadido al prompt.")

            except Exception as e:
                logging.error(f"Error al subir el archivo {upload_file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"Error al procesar el archivo {upload_file.filename}.")

    if youtube_url and "youtube.com" in youtube_url:
        try:
            youtube_part = types.Part(file_data=types.FileData(file_uri=youtube_url))
            contents.append(youtube_part)
            processed_youtube_urls.append(youtube_url)
            logging.info(f"URL de YouTube {youtube_url} añadida al prompt.")
        except Exception as e:
            logging.error(f"Error al procesar la URL de YouTube {youtube_url}: {e}")
            raise HTTPException(status_code=500, detail=f"URL de YouTube inválida o no accesible.")

    if processed_attachments or processed_youtube_urls:
        request.multimodal_resources = MultimodalResources(
            youtube_urls=processed_youtube_urls if processed_youtube_urls else None,
            attachments=processed_attachments if processed_attachments else None
        )

    return StreamingResponse(
        stream_generator(
            contents=contents,
            request_data=request,
            user_id=current_user.id,
            db=db
        ),
        media_type="text/event-stream"
    )

@router.get(
    "/history/me",
    response_model=List[PlanningLogResponse],
    summary="Obtener historial de planificaciones del usuario",
    description="Devuelve una lista de todas las planificaciones generadas por el usuario actualmente autenticado, ordenadas de la más reciente a la más antigua."
)
def get_user_planning_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    history = planning_crud.get_planning_logs_by_user_id(db, user_id=current_user.id)
    return history

@router.get(
    "/history/{planning_id}",
    response_model=PlanningLogDetailResponse,
    summary="Obtener detalle de una planificación específica",
    description="Devuelve los detalles completos de un registro de planificación, solo si pertenece al usuario autenticado.",
    responses={404: {"description": "La planificación no fue encontrada o no pertenece al usuario."}}
)
def get_planning_detail(
    planning_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    log_detail = planning_crud.get_planning_log_by_id_for_user(
        db, planning_id=planning_id, user_id=current_user.id
    )
    if not log_detail:
        raise HTTPException(status_code=404, detail="Planificación no encontrada.")
    return log_detail