from sqlalchemy.orm import Session
from . import models as db_models

def create_planning_log(
    db: Session,
    user_id: int,
    oa_codigo: str,
    cost: float,
    input_tokens: int,
    output_tokens: int,
    thought_tokens: int,
):
    db_log = db_models.PlanningLog(
        user_id=user_id,
        oa_codigo=oa_codigo,
        cost=cost,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        thought_tokens=thought_tokens,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_planning_logs_by_user_id(db: Session, user_id: int):
    """
    Obtiene todos los registros de planificación para un usuario específico,
    ordenados del más reciente al más antiguo.
    """
    return (
        db.query(db_models.PlanningLog)
        .filter(db_models.PlanningLog.user_id == user_id)
        .order_by(db_models.PlanningLog.timestamp.desc())
        .all()
    )

def get_planning_log_by_id_for_user(db: Session, planning_id: int, user_id: int):
    """
    Obtiene un registro de planificación específico por su ID,
    asegurándose de que pertenezca al usuario especificado.
    """
    return (
        db.query(db_models.PlanningLog)
        .filter(
            db_models.PlanningLog.id == planning_id,
            db_models.PlanningLog.user_id == user_id
        )
        .first()
    )