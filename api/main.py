import logging
import sys
from fastapi import FastAPI
from .routers import curriculum, planning

# --- Configuración de Logging ---
# Configura el logger raíz para que los logs de los módulos aparezcan en la consola de uvicorn
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

app = FastAPI(
    title="API de Planificación Curricular",
    description="API para consultar y utilizar los datos del currículum nacional chileno, enriquecidos con IA, para generar planificaciones de clase.",
    version="2.0.0",
)

app.include_router(curriculum.router)
app.include_router(planning.router)

@app.get("/", tags=["General"])
def read_root():
    """
    Endpoint raíz que devuelve un mensaje de bienvenida.
    """
    return {"message": "Bienvenido a la API de Planificación Curricular v2.0"}
