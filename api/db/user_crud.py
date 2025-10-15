from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from .. import models as pydantic_models
from ..db import models as db_models
from ..core import security

def get_user_by_username(db: Session, username: str) -> db_models.User:
    return db.query(db_models.User).filter(db_models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> db_models.User:
    return db.query(db_models.User).filter(db_models.User.email == email).first()

def create_user(db: Session, user: pydantic_models.UserCreate) -> db_models.User:
    hashed_password = security.get_password_hash(user.password)
    db_user = db_models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=False,
        role="user"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_status(db: Session, user: db_models.User, is_active: bool) -> db_models.User:
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user

def update_user_role(db: Session, user: db_models.User, role: str) -> db_models.User:
    user.role = role
    db.commit()
    db.refresh(user)
    return user

# --- Funciones para el Dashboard de Administración ---

def get_total_user_count(db: Session) -> int:
    return db.query(db_models.User).count()

def get_users_with_cost_summary(db: Session):
    """
    Calcula el costo total y el número de planificaciones para cada usuario.
    """
    return (
        db.query(
            db_models.User.username,
            func.sum(db_models.PlanningLog.cost).label("total_cost"),
            func.count(db_models.PlanningLog.id).label("total_plannings"),
        )
        .outerjoin(db_models.PlanningLog, db_models.User.id == db_models.PlanningLog.user_id)
        .group_by(db_models.User.username)
        .all()
    )