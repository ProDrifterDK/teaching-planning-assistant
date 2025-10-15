import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import curriculum, planning, auth
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
            user_crud.update_user_status(db, new_admin, is_active=True)
            # Le asignamos el rol de admin
            new_admin.role = "admin"
            db.commit()
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
    title="API de Planificación Curricular",
    description="API para consultar y utilizar los datos del currículum nacional chileno, enriquecidos con IA.",
    version="2.1.0",
    lifespan=lifespan
)

# --- Configuración de CORS ---
origins = [
    "http://localhost:3000", # Origen del frontend de Next.js
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # Permite todas las cabeceras (incluyendo Authorization)
)

app.include_router(curriculum.router)
app.include_router(planning.router)
app.include_router(auth.router)

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Bienvenido a la API de Planificación Curricular v2.1"}
