"""
Arquivo: app/modules/health/routes.py

Responsabilidade:
Endpoints de health check para monitoramento e readiness.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
import redis
import time
from datetime import datetime

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
def health_check():
    """
    Health check básico - retorna se a aplicação está rodando.
    Usado por load balancers para verificar se o serviço está up.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "app_name": settings.app_name
    }


@router.get("/readiness")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - verifica se a aplicação está pronta para receber tráfego.
    Valida:
    - Conexão com banco de dados
    - Conexão com Redis
    - Configurações críticas
    """
    checks = {}
    all_healthy = True

    # Check database
    try:
        start = time.time()
        db.execute("SELECT 1")
        elapsed = time.time() - start
        checks["database"] = {
            "status": "healthy",
            "latency_ms": round(elapsed * 1000, 2)
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        all_healthy = False

    # Check Redis
    try:
        start = time.time()
        r = redis.from_url(settings.redis_url)
        r.ping()
        elapsed = time.time() - start
        checks["redis"] = {
            "status": "healthy",
            "latency_ms": round(elapsed * 1000, 2)
        }
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        all_healthy = False

    # Check configuration
    config_issues = []
    if settings.is_production():
        if settings.secret_key == "change-me":
            config_issues.append("SECRET_KEY is default value")
        if "*" in settings.cors_allow_origins:
            config_issues.append("CORS allows all origins")

    checks["configuration"] = {
        "status": "healthy" if not config_issues else "warning",
        "issues": config_issues
    }

    if config_issues and settings.is_production():
        all_healthy = False

    status_code = 200 if all_healthy else 503

    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/liveness")
def liveness_check():
    """
    Liveness check - verifica se a aplicação está viva.
    Se este endpoint falhar, o container deve ser reiniciado.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
def metrics():
    """
    Métricas básicas do sistema.
    Pode ser expandido para formato Prometheus.
    """
    import psutil

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
