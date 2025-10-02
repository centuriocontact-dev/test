# app/core/logger.py
"""
Logging structuré JSON pour production
Compatible avec les systèmes de monitoring cloud (Datadog, New Relic, etc.)
"""
import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import uuid

# Context variables pour tracer les requêtes
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
client_id_var: ContextVar[Optional[str]] = ContextVar('client_id', default=None)

class JSONFormatter(logging.Formatter):
    """Formatter pour logs structurés JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Ajouter le contexte de la requête
        request_id = request_id_var.get()
        if request_id:
            log_data['request_id'] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data['user_id'] = user_id
        
        client_id = client_id_var.get()
        if client_id:
            log_data['client_id'] = client_id
        
        # Ajouter l'exception si présente
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown',
                'message': str(record.exc_info[1]) if record.exc_info[1] else '',
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Ajouter les données extra
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        # Masquer les données sensibles
        log_data = self._mask_sensitive_data(log_data)
        
        return json.dumps(log_data, ensure_ascii=False)
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Masque les données sensibles dans les logs"""
        sensitive_keys = {
            'password', 'pwd', 'pass', 'secret', 'token', 
            'api_key', 'apikey', 'auth', 'authorization',
            'cookie', 'session', 'credit_card', 'cc_number',
            'cvv', 'ssn', 'pin'
        }
        
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    masked_data[key] = '***MASKED***'
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            # Masquer les tokens JWT
            if data.startswith('Bearer ') and len(data) > 20:
                return 'Bearer ***MASKED***'
            # Masquer les emails partiellement
            if '@' in data and '.' in data:
                parts = data.split('@')
                if len(parts) == 2:
                    return f"{parts[0][:2]}***@{parts[1]}"
        return data

class StructuredLogger:
    """Logger avec support pour logs structurés"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        # Configurer le handler si pas déjà fait
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Désactiver la propagation pour éviter les doublons
        self.logger.propagate = False
    
    def _log(self, level: int, message: str, extra: Optional[Dict] = None, exc_info=None):
        """Log avec données extra"""
        log_record = self.logger.makeRecord(
            self.logger.name,
            level,
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=exc_info
        )
        
        if extra:
            log_record.extra_data = extra
        
        self.logger.handle(log_record)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, kwargs)
    
    def error(self, message: str, exc_info=None, **kwargs):
        self._log(logging.ERROR, message, kwargs, exc_info=exc_info)
    
    def critical(self, message: str, exc_info=None, **kwargs):
        self._log(logging.CRITICAL, message, kwargs, exc_info=exc_info)

# Logger pour différents modules
auth_logger = StructuredLogger('auth')
matching_logger = StructuredLogger('matching')
security_logger = StructuredLogger('security')
performance_logger = StructuredLogger('performance')
business_logger = StructuredLogger('business')

# Middleware pour ajouter request_id
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logging des requêtes et performances"""
    
    async def dispatch(self, request: Request, call_next):
        # Générer un request_id unique
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Récupérer user_id et client_id depuis le token si présent
        # (implémentation dépend de votre système d'auth)
        
        # Logger le début de la requête
        start_time = time.time()
        
        # Log de la requête entrante
        performance_logger.info(
            f"Request started: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None
        )
        
        try:
            # Traiter la requête
            response = await call_next(request)
            
            # Calculer le temps de traitement
            process_time = (time.time() - start_time) * 1000  # en ms
            
            # Logger la réponse
            performance_logger.info(
                f"Request completed: {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time_ms=round(process_time, 2),
                request_id=request_id
            )
            
            # Ajouter le request_id au header de réponse
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            
            # Alertes pour performances dégradées
            if process_time > 1000:  # Plus d'1 seconde
                performance_logger.warning(
                    f"Slow request detected: {request.method} {request.url.path}",
                    method=request.method,
                    path=request.url.path,
                    process_time_ms=round(process_time, 2)
                )
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            
            # Logger l'erreur
            performance_logger.error(
                f"Request failed: {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                process_time_ms=round(process_time, 2),
                request_id=request_id,
                exc_info=e
            )
            raise

# Fonctions utilitaires pour logging métier
def log_auth_attempt(email: str, success: bool, reason: Optional[str] = None):
    """Log une tentative d'authentification"""
    auth_logger.info(
        f"Authentication {'succeeded' if success else 'failed'} for {email}",
        email=email,
        success=success,
        reason=reason
    )

def log_matching_execution(client_id: str, besoin_id: Optional[str], 
                          candidats_count: int, duration_ms: float, 
                          use_ai: bool = False):
    """Log l'exécution d'un matching"""
    matching_logger.info(
        "Matching executed",
        client_id=client_id,
        besoin_id=besoin_id,
        candidats_analyzed=candidats_count,
        duration_ms=round(duration_ms, 2),
        use_ai=use_ai
    )

def log_security_event(event_type: str, details: Dict, severity: str = "warning"):
    """Log un événement de sécurité"""
    log_func = getattr(security_logger, severity, security_logger.warning)
    log_func(
        f"Security event: {event_type}",
        event_type=event_type,
        **details
    )

def log_business_metric(metric_name: str, value: Any, metadata: Optional[Dict] = None):
    """Log une métrique business"""
    data = {'metric': metric_name, 'value': value}
    if metadata:
        data.update(metadata)
    business_logger.info(f"Business metric: {metric_name}", **data)

# Configuration pour différents environnements
def setup_logging(environment: str):
    """Configure le logging selon l'environnement"""
    if environment == "production":
        # En production, tout en JSON
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        
        # Désactiver les logs verbeux de certaines libs
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        
    elif environment == "development":
        # En dev, format plus lisible
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    else:  # test
        # En test, niveau ERROR seulement
        logging.basicConfig(level=logging.ERROR)