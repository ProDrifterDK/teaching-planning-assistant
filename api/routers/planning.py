from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from google.genai import types
import google.genai as genai
import logging
import json
from ..models import PlanRequest, StreamThought, StreamAnswer
from ..core.config import settings
from ..core.pricing import calculate_cost
from ..services.curriculum_service import CurriculumService, get_curriculum_service

router = APIRouter(
    prefix="/planning",
    tags=["Co-piloto de Planificación"]
)

async def stream_generator(prompt: str, oa_codigo: str):
    """
    Generador asíncrono que produce fragmentos de la respuesta de Gemini (pensamientos y respuesta final).
    Registra el costo total al finalizar el stream.
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
            logging.info(f"Stream finalizado para OA '{oa_codigo}'. Costo: ${cost:.6f}, Tokens(I/O/T): {input_tokens}/{output_tokens}/{thought_tokens}")

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
    service: CurriculumService = Depends(get_curriculum_service)
):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="La API de Gemini no está configurada.")

    oa_details = service.find_oa_details(request.oa_codigo_oficial)
    if not oa_details:
        raise HTTPException(status_code=404, detail=f"OA '{request.oa_codigo_oficial}' no encontrado.")
    
    oa_completo = oa_details["oa_completo"]
    contexto_asignatura = oa_details["contexto_asignatura"]
    eje = oa_details["eje"]
    
    prompt = f"""
    Rol: Actúa como un experto en diseño instruccional y un co-piloto para un profesor chileno de educación básica o media. Tu objetivo es crear una planificación de clase completa, lista para ser usada.

    Contexto Curricular:
    - Asignatura: {contexto_asignatura.get('asignatura', 'N/A')}
    - Curso: {contexto_asignatura.get('curso', 'N/A')}
    - Eje Curricular: {eje.get('nombre_eje', 'N/A')}
    - Objetivo de Aprendizaje (OA) a tratar:
        - Código: {oa_completo.get('oa_codigo_oficial', 'N/A')}
        - Descripción: {oa_completo.get('descripcion_oa', 'N/A')}
        - Componentes Clave: {', '.join(oa_completo.get('desglose_componentes', []))}
        - Habilidades de Bloom: {', '.join(oa_completo.get('habilidades', []))}
    - Actitudes a Fomentar: {[act.get('descripcion', '') for act in contexto_asignatura.get('actitudes', [])]}

    Contexto del Profesor:
    - Recurso Principal: {request.recurso_principal}
    - Nivel Real de los Estudiantes: {request.nivel_real_estudiantes}
    - Duración de la Clase: 90 minutos.

    Instrucciones de Salida:
    Genera una planificación de clase en formato Markdown. La planificación debe ser completa y estar estructurada en tres fases claras: Inicio (15-20 min), Desarrollo (50-60 min) y Cierre (10-15 min). Debe incluir actividades concretas, distribución del tiempo, y al menos una sugerencia de evaluación formativa. Sé creativo y práctico.
    """

    return StreamingResponse(stream_generator(prompt, request.oa_codigo_oficial), media_type="text/event-stream")