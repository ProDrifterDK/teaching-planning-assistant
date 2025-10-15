import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..db.session import get_db
from ..models import AdminDashboardStats, UserCostSummary, User
from ..db import user_crud
from .auth import get_current_admin_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(get_current_admin_user)],
)

@router.get("/dashboard-stats", response_model=AdminDashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Recopila y devuelve estadísticas agregadas para el dashboard de administración.
    """
    total_users = user_crud.get_total_user_count(db)
    users_summary_data = user_crud.get_users_with_cost_summary(db)

    users_summary: List[UserCostSummary] = []
    total_system_cost = 0.0
    total_system_plannings = 0

    for item in users_summary_data:
        # Los resultados de una query agrupada pueden tener None si no hay logs
        cost = item.total_cost or 0.0
        plannings = item.total_plannings or 0

        users_summary.append(
            UserCostSummary(
                username=item.username,
                total_cost=cost,
                total_plannings=plannings,
                is_active=item.is_active,
                role=item.role,
            )
        )
        total_system_cost += cost
        total_system_plannings += plannings
    
    response_data = AdminDashboardStats(
        total_users=total_users,
        total_system_cost=total_system_cost,
        total_system_plannings=total_system_plannings,
        users_summary=users_summary,
    )
    
    logging.info(f"Admin dashboard data sent: {response_data.json()}")
    
    return response_data