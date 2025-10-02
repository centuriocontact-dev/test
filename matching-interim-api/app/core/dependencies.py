# app/core/dependencies.py
from fastapi import Depends
from app.core.security import get_current_user
from app.models.models import User

def get_current_client_id(current_user: User = Depends(get_current_user)) -> str:
    """Récupère le client_id de l'utilisateur courant"""
    return str(current_user.client_id)
