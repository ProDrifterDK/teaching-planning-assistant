from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from typing import Optional
import psutil
import os

from api.db.session import get_async_db
from api.core.config import settings

router = APIRouter(tags=["Health"])

class HealthStatus:
    """Health check status constants"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns 200 if the service is running.
    Used by load balancers and orchestration tools.
    """
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "teaching-planning-assistant",
        "version": getattr(settings, 'VERSION', '1.0.0')
    }

@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe.
    
    Returns 200 if the process is alive.
    Failure causes container restart.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_async_db)):
    """
    Kubernetes readiness probe.
    
    Returns 200 if the service is ready to accept traffic.
    Checks database connectivity and essential services.
    """
    checks = {
        "database": await _check_database(db),
        "gemini_api": await _check_gemini_api(),
        "memory": _check_memory(),
        "disk": _check_disk()
    }
    
    # Determine overall status
    all_healthy = all(c["status"] == HealthStatus.HEALTHY for c in checks.values())
    any_unhealthy = any(c["status"] == HealthStatus.UNHEALTHY for c in checks.values())
    
    if all_healthy:
        overall_status = HealthStatus.HEALTHY
    elif any_unhealthy:
        overall_status = HealthStatus.UNHEALTHY
    else:
        overall_status = HealthStatus.DEGRADED
    
    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
    
    return response

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_async_db)):
    """
    Detailed health check with system metrics.
    
    Provides comprehensive system status for monitoring.
    Should be protected in production.
    """
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.utcnow().isoformat(),
        "service": {
            "name": "teaching-planning-assistant",
            "version": getattr(settings, 'VERSION', '1.0.0'),
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory": {
                "total_mb": psutil.virtual_memory().total / (1024 * 1024),
                "available_mb": psutil.virtual_memory().available / (1024 * 1024),
                "percent_used": psutil.virtual_memory().percent
            },
            "disk": {
                "total_gb": psutil.disk_usage('/').total / (1024 * 1024 * 1024),
                "free_gb": psutil.disk_usage('/').free / (1024 * 1024 * 1024),
                "percent_used": psutil.disk_usage('/').percent
            }
        },
        "checks": {
            "database": await _check_database(db),
            "gemini_api": await _check_gemini_api()
        }
    }

async def _check_database(db: AsyncSession) -> dict:
    """Check database connectivity"""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": HealthStatus.HEALTHY,
            "message": "Database connection OK"
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"Database error: {str(e)}"
        }

async def _check_gemini_api() -> dict:
    """Check Gemini API availability"""
    try:
        import google.generativeai as genai
        from api.core.config import settings
        
        if not settings.GEMINI_API_KEY:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": "GEMINI_API_KEY not configured"
            }
        
        # Simple check - just verify API key format
        if len(settings.GEMINI_API_KEY) > 10:
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Gemini API key configured"
            }
        
        return {
            "status": HealthStatus.DEGRADED,
            "message": "Gemini API key may be invalid"
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"Gemini API check failed: {str(e)}"
        }

def _check_memory() -> dict:
    """Check memory usage"""
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"High memory usage: {memory.percent}%"
        }
    elif memory.percent > 75:
        return {
            "status": HealthStatus.DEGRADED,
            "message": f"Elevated memory usage: {memory.percent}%"
        }
    return {
        "status": HealthStatus.HEALTHY,
        "message": f"Memory usage OK: {memory.percent}%"
    }

def _check_disk() -> dict:
    """Check disk usage"""
    disk = psutil.disk_usage('/')
    if disk.percent > 90:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"High disk usage: {disk.percent}%"
        }
    elif disk.percent > 75:
        return {
            "status": HealthStatus.DEGRADED,
            "message": f"Elevated disk usage: {disk.percent}%"
        }
    return {
        "status": HealthStatus.HEALTHY,
        "message": f"Disk usage OK: {disk.percent}%"
    }