# app/routers/health.py
"""
Health check endpoints pour monitoring en production
Compatible avec les health checks de Render.com et autres plateformes cloud
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import os
import psutil
import time
from typing import Dict, Any

from app.database import get_db
from app.config import settings
from app.models.models import Candidat, Besoin, User

router = APIRouter(tags=["Health"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Health check basique - toujours retourne 200 si l'app est accessible
    Utilisé par les load balancers et monitoring
    """
    return {
        "status": "healthy",
        "service": "matching-interim-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@router.get("/health/db")
async def health_check_database(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check de la base de données
    Vérifie la connexion et les performances
    """
    start_time = time.time()
    
    try:
        # Test de connexion simple
        result = db.execute(text("SELECT 1")).scalar()
        
        # Récupérer quelques stats
        candidats_count = db.query(Candidat).count()
        besoins_count = db.query(Besoin).count()
        users_count = db.query(User).count()
        
        # Temps de réponse
        response_time = (time.time() - start_time) * 1000  # en ms
        
        # Statut basé sur le temps de réponse
        if response_time < 100:
            db_status = "healthy"
        elif response_time < 500:
            db_status = "degraded"
        else:
            db_status = "unhealthy"
        
        return {
            "status": db_status,
            "database": "postgresql",
            "connected": True,
            "response_time_ms": round(response_time, 2),
            "stats": {
                "candidats": candidats_count,
                "besoins": besoins_count,
                "users": users_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "postgresql",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/health/openai")
async def health_check_openai() -> Dict[str, Any]:
    """
    Health check pour l'API OpenAI (si utilisée)
    """
    if not settings.USE_OPENAI:
        return {
            "status": "disabled",
            "service": "openai",
            "message": "OpenAI integration is disabled",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        import openai
        
        start_time = time.time()
        
        # Test simple avec un modèle léger
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            temperature=0
        )
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "service": "openai",
            "connected": True,
            "response_time_ms": round(response_time, 2),
            "model": "gpt-3.5-turbo",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "openai",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/health/detailed")
async def health_check_detailed(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check détaillé avec métriques système
    Pour monitoring avancé et debugging
    """
    checks = {}
    overall_status = "healthy"
    
    # 1. Check App Status
    checks["app"] = {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "uptime_seconds": time.time() - app_start_time if 'app_start_time' in globals() else None
    }
    
    # 2. Check Database
    try:
        start = time.time()
        db.execute(text("SELECT 1"))
        db_time = (time.time() - start) * 1000
        
        checks["database"] = {
            "status": "healthy" if db_time < 500 else "degraded",
            "response_time_ms": round(db_time, 2),
            "pool_size": getattr(db.bind.pool, 'size', 'N/A') if hasattr(db.bind, 'pool') else 'N/A'
        }
        
        if db_time > 500:
            overall_status = "degraded"
            
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "unhealthy"
    
    # 3. Check System Resources
    try:
        process = psutil.Process()
        memory = psutil.virtual_memory()
        
        checks["system"] = {
            "status": "healthy",
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": memory.percent,
            "memory_available_mb": round(memory.available / 1024 / 1024),
            "process_memory_mb": round(process.memory_info().rss / 1024 / 1024),
            "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 'N/A',
            "num_threads": process.num_threads()
        }
        
        # Alerte si ressources élevées
        if memory.percent > 90 or psutil.cpu_percent() > 90:
            checks["system"]["status"] = "degraded"
            overall_status = "degraded" if overall_status == "healthy" else overall_status
            
    except Exception as e:
        checks["system"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # 4. Check Storage (uploads directory)
    try:
        uploads_path = "uploads"
        if os.path.exists(uploads_path):
            stat = os.statvfs(uploads_path)
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
            used_percent = ((total_gb - free_gb) / total_gb) * 100
            
            checks["storage"] = {
                "status": "healthy" if used_percent < 80 else "degraded",
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_percent, 2)
            }
            
            if used_percent > 80:
                overall_status = "degraded" if overall_status == "healthy" else overall_status
        else:
            checks["storage"] = {
                "status": "unknown",
                "message": "uploads directory not found"
            }
            
    except Exception as e:
        checks["storage"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # 5. Check External Services
    checks["external_services"] = {}
    
    # OpenAI check (if enabled)
    if settings.USE_OPENAI:
        try:
            # Quick check without actual API call
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            checks["external_services"]["openai"] = {
                "status": "configured",
                "has_key": bool(settings.OPENAI_API_KEY)
            }
        except Exception as e:
            checks["external_services"]["openai"] = {
                "status": "error",
                "error": str(e)
            }
    
    # Redis check (if configured)
    if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            checks["external_services"]["redis"] = {
                "status": "healthy"
            }
        except Exception as e:
            checks["external_services"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_status = "degraded" if overall_status == "healthy" else overall_status
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness probe - indique si l'app est prête à recevoir du trafic
    Utilisé par Kubernetes/orchestrateurs
    """
    ready = True
    checks_passed = []
    checks_failed = []
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks_passed.append("database")
    except Exception:
        checks_failed.append("database")
        ready = False
    
    # Check required directories
    required_dirs = ["uploads", "uploads/candidats", "uploads/besoins", "data"]
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.access(dir_path, os.W_OK):
            checks_passed.append(f"dir:{dir_path}")
        else:
            checks_failed.append(f"dir:{dir_path}")
            ready = False
    
    if ready:
        return {
            "ready": True,
            "checks_passed": checks_passed,
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ready": False,
                "checks_passed": checks_passed,
                "checks_failed": checks_failed,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness probe - indique si l'app est vivante (pas bloquée)
    Retourne toujours 200 sauf si l'app est vraiment bloquée
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }

# Variable globale pour uptime (initialisée au démarrage)
app_start_time = time.time()