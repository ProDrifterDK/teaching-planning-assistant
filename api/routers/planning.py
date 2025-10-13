from fastapi import APIRouter, Depends, HTTPException
import google.generativeai as genai
import logging
from ..models import PlanRequest, PlanResponse
from ..core.config import settings
from ..core.pricing import calculate_cost
from ..services.curriculum_service import CurriculumService, get_curriculum_service

router = APIRouter(
    prefix="/planning",
    tags=["Co-piloto de Planificación"]
)

@router.on_event("startup")
def configure_genai():
    """Configura la API de Google Gemini al iniciar."""
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    else:
        # Esto podría ser un error crítico en producción
        print("Advertencia: GEMINI_API_KEY no está configurada.")

@router.post("/generate-plan", response_model=PlanResponse)
async def generate_plan(
    request: PlanRequest,
    service: CurriculumService = Depends(get_curriculum_service)
):
    """
    Genera una planificación de clase detallada para un OA específico.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="La API de Gemini no está configurada en el servidor.")

    # 1. Buscar el OA completo en nuestros datos
    oa_details = service.find_oa_details(request.oa_codigo_oficial)
    
    if not oa_details:
        raise HTTPException(status_code=404, detail=f"OA con código '{request.oa_codigo_oficial}' no encontrado.")
    
    oa_completo = oa_details["oa_completo"]
    contexto_asignatura = oa_details["contexto_asignatura"]
    eje = oa_details["eje"]
    
    # 2. Construir el Prompt Enriquecido
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
    
    # 3. Llamar a la API de Gemini
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Configuración para maximizar la respuesta y el razonamiento
        generation_config = genai.GenerationConfig(
            max_output_tokens=8192
        )
        thinking_config = genai.types.ThinkingConfig(
            thinking_budget=-1,  # Activar pensamiento dinámico
            include_thoughts=True
        )
        
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config,
            thinking_config=thinking_config
        )
        
        # 4. Devolver la respuesta
        # 4. Calcular costos y registrar
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            thought_tokens = response.usage_metadata.thoughts_token_count if hasattr(response.usage_metadata, 'thoughts_token_count') else 0
            
            cost = calculate_cost(input_tokens, output_tokens + thought_tokens)
            logging.info(f"Plan generado para OA '{request.oa_codigo_oficial}'. Costo: ${cost:.6f}, Tokens(I/O/T): {input_tokens}/{output_tokens}/{thought_tokens}")
        
        # 5. Devolver la respuesta
        return {"planificacion": response.text}
    except Exception as e:
        logging.error(f"Error al generar la planificación para OA '{request.oa_codigo_oficial}': {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar la planificación desde la API de Gemini: {str(e)}")