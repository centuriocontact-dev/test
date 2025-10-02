# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from app.config import settings
from app.database import engine
from app.models.models import Base
from app.routers import auth, candidats, besoins, matchings, uploads
from app.core.middleware import LoggingMiddleware

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie"""
    logger.info("🚀 Démarrage Matching Intérim API")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    
    # Créer les dossiers nécessaires
    import os
    os.makedirs("uploads/candidats", exist_ok=True)
    os.makedirs("uploads/besoins", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    yield
    
    logger.info("🛑 Arrêt de l'application")

# Application FastAPI
app = FastAPI(
    title="Matching Intérim Pro API",
    description="API de matching intelligent candidats-besoins",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware custom
app.add_middleware(LoggingMiddleware)

# Middleware timing
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur"}
    )

# Routes
@app.get("/")
async def root():
    return {
        "application": "Matching Intérim Pro API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check pour monitoring"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

# Inclusion des routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(candidats.router, prefix="/api/candidats", tags=["Candidats"])
app.include_router(besoins.router, prefix="/api/besoins", tags=["Besoins"])
app.include_router(matchings.router, prefix="/api/matchings", tags=["Matchings"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Uploads"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )