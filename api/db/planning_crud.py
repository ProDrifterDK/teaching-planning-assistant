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