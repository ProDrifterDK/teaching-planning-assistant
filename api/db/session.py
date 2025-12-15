from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# La URL de la base de datos SQLite.
# El archivo 'app.db' se creará en el directorio raíz de la API.
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
SQLALCHEMY_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./app.db"

# El 'engine' es el punto de entrada a la base de datos.
# El argumento 'connect_args' es necesario solo para SQLite para permitir
# múltiples hilos (como los que usa FastAPI).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

async_engine = create_async_engine(
    SQLALCHEMY_ASYNC_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Cada instancia de SessionLocal será una sesión de base de datos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

# Usaremos esta Base para crear cada uno de los modelos ORM (las tablas).
Base = declarative_base()

# Dependencia para obtener una sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    async with AsyncSessionLocal() as db:
        yield db