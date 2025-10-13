from fastapi import FastAPI
from .routers import curriculum, planning
from .services.curriculum_service import curriculum_service # Importar la instancia

app = FastAPI(
    title="API de Planificación Curricular",
    description="API para consultar y utilizar los datos del currículum nacional chileno, enriquecidos con IA, para generar planificaciones de clase.",
    version="2.0.0",
    contact={
        "name": "Equipo de Desarrollo",
        "url": "http://example.com/contact",
        "email": "dev@example.com",
    },
)

# --- Carga de Datos ---
# La carga de datos se maneja ahora dentro del módulo de servicio (singleton).
# El evento 'startup' en el router de planning se encargará de configurar Gemini.

# --- Inclusión de Routers ---
app.include_router(curriculum.router)
app.include_router(planning.router)

@app.get("/", tags=["General"])
def read_root():
    """
    Endpoint raíz que devuelve un mensaje de bienvenida.
    Útil para verificar que la API está funcionando.
    """
    return {"message": "Bienvenido a la API de Planificación Curricular v2.0"}
