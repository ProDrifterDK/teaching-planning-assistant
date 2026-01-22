import logging
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import new components
from api.routers import health
from api.middleware.rate_limit import RateLimitMiddleware

from .routers import admin, auth, curriculum, planning, export, apikeys, content, validation, batch, tutor, revision
from .db.session import engine, SessionLocal
from .db import models as db_models, user_crud
from .db.apikey_crud import create_service_client, list_service_clients, hash_api_key
from .models import UserCreate

# Esta función se ejecuta al iniciar la aplicación
def create_initial_admin_user():
    db = SessionLocal()
    try:
        # Verificar si el usuario admin ya existe
        admin_user = user_crud.get_user_by_username(db, "admin")
        if not admin_user:
            logging.info("Usuario 'admin' no encontrado, creando usuario administrador inicial...")
            admin_user_in = UserCreate(
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                password="adminpass" # Contraseña para el admin
            )
            # Creamos el usuario a través del CRUD
            new_admin = user_crud.create_user(db, admin_user_in)
            # Lo activamos inmediatamente
            user_crud.update_user_status(db, user=new_admin, is_active=True)
            # Le asignamos el rol de admin
            user_crud.update_user_role(db, user=new_admin, role="admin")
            logging.info("Usuario administrador 'admin' creado y activado exitosamente.")
        else:
            logging.info("Usuario administrador 'admin' ya existe.")
    finally:
        db.close()

def create_initial_api_keys():
    """Create API keys for known clients on startup if they don't exist.
    Uses environment variables for pre-defined API keys to maintain consistency across deploys."""
    db = SessionLocal()
    try:
        existing_clients = list_service_clients(db)
        existing_names = [c.client_name for c in existing_clients]
        
        # Check for Colegio Alas client
        if "colegio-alas-prod" not in existing_names:
            # Get pre-defined API key from environment, or generate a new one
            predefined_key = os.getenv("COLEGIO_ALAS_API_KEY")
            
            if predefined_key:
                # Use predefined key from environment
                logging.info("Creating 'colegio-alas-prod' API client with predefined key from environment...")
                api_key_hash = hash_api_key(predefined_key)
                
                db_client = db_models.ServiceClient(
                    client_name="colegio-alas-prod",
                    api_key_hash=api_key_hash,
                    permissions=["batch:create", "batch:read", "generate:quiz", "generate:activity",
                                "generate:exam", "generate:reinforcement", "generate:lesson",
                                "content:generate", "content:adapt", "planning:generate"],
                    rate_limit=200,
                    webhook_url=None
                )
                db.add(db_client)
                db.commit()
                logging.info("✅ 'colegio-alas-prod' API client created successfully with predefined key.")
            else:
                # Generate new key (warning: this won't match existing configs)
                logging.warning("COLEGIO_ALAS_API_KEY not set in environment. Generating new key...")
                client, raw_key = create_service_client(
                    db,
                    client_name="colegio-alas-prod",
                    permissions=["batch:create", "batch:read", "generate:quiz", "generate:activity",
                                "generate:exam", "generate:reinforcement", "generate:lesson",
                                "content:generate", "content:adapt", "planning:generate"],
                    rate_limit=200,
                    webhook_url=None
                )
                logging.warning(f"⚠️ New API key generated. Update COLEGIO_ALAS_API_KEY env var with: {raw_key}")
        else:
            logging.info("API client 'colegio-alas-prod' already exists.")
            
    except Exception as e:
        logging.error(f"Error creating initial API keys: {e}")
    finally:
        db.close()

# -- Lifespan Events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Esto se ejecuta al iniciar la aplicación
    logging.info("Iniciando aplicación y creando tablas de base de datos...")
    db_models.Base.metadata.create_all(bind=engine)
    create_initial_admin_user()
    create_initial_api_keys()
    yield
    # Esto se ejecuta al apagar la aplicación (si es necesario)
    logging.info("Apagando aplicación...")

# --- Configuración de Logging y App ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

app = FastAPI(
    title="Teaching Planning Assistant API",
    description="Autonomous educational content generation engine for Chilean curriculum",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware (order matters - rate limit should be early)
app.add_middleware(RateLimitMiddleware)

# --- Configuración de CORS ---
origins = [
    "http://localhost:3000", # Origen del frontend de Next.js en desarrollo
    "https://teaching-planning-assistant-fronten.vercel.app", # Origen del frontend desplegado en Vercel
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # Permite todas las cabeceras (incluyendo Authorization)
)

# Include health router (without prefix for standard paths)
app.include_router(health.router)

app.include_router(curriculum.router)
app.include_router(planning.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(export.router)
app.include_router(apikeys.router)
app.include_router(content.router)
app.include_router(validation.router)
app.include_router(batch.router)
app.include_router(tutor.router)
app.include_router(revision.router)

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Bienvenido a la API de Planificación Curricular v2.1"}
