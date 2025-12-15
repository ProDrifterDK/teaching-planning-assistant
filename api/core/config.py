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
    
    # --- JWT Settings ---
    # Para generar una buena clave secreta, puedes usar: openssl rand -hex 32
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_super_secret_key_for_development")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 60
    RATE_LIMIT_API_KEY_PER_MINUTE: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Service Info
    VERSION: str = "2.0.0"  # New version with Colegio Alas integration
    SERVICE_NAME: str = "teaching-planning-assistant"

    class Config:
        env_file = ".env"
        # Esto permite que Pydantic ignore campos extra si se definen en el .env
        extra = 'ignore'

# Instancia única de la configuración para ser usada en toda la app
settings = Settings()