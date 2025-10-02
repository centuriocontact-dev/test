# app/core/middleware.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger les requêtes"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log requête
        logger.info(f"➡️  {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Log réponse
        process_time = time.time() - start_time
        logger.info(
            f"⬅️  {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        return response