import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Carga las variables de entorno desde un archivo .env
load_dotenv()

class Settings(BaseSettings):
    """
    Configuraciones de la aplicación cargadas desde el entorno.
    """
    APP_NAME: str = "API de Planificación Curricular"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    class Config:
        # Esto permite que Pydantic lea desde un archivo .env si es necesario,
        # aunque ya lo estamos haciendo con load_dotenv. Es una buena práctica.
        env_file = ".env"

# Instancia única de la configuración para ser usada en toda la app
settings = Settings()