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

    # AI provider settings. Defaults target DeepSeek's OpenAI-compatible endpoint.
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "deepseek")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    AI_API_KEY: str = os.getenv("AI_API_KEY") or DEEPSEEK_API_KEY
    AI_BASE_URL: str = os.getenv("AI_BASE_URL") or DEEPSEEK_BASE_URL
    AI_MODEL: str = os.getenv("AI_MODEL") or DEEPSEEK_MODEL
    AI_REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "120"))
    AI_MAX_OUTPUT_TOKENS: int = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "16000"))
    
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