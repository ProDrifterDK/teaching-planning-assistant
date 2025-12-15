import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import new components
from api.routers import health
from api.middleware.rate_limit import RateLimitMiddleware

from .routers import admin, auth, curriculum, planning, export, apikeys, content, validation, batch, tutor
from .db.session import engine, SessionLocal
from .db import models as db_models, user_crud
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

# -- Lifespan Events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Esto se ejecuta al iniciar la aplicación
    logging.info("Iniciando aplicación y creando tablas de base de datos...")
    db_models.Base.metadata.create_all(bind=engine)
    create_initial_admin_user()
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

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Bienvenido a la API de Planificación Curricular v2.1"}
