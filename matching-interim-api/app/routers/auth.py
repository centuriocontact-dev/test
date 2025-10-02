# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models.models import User, Session as SessionModel
from app.schemas.auth import Token, LoginResponse
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user
)

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Connexion utilisateur
    """
    # Récupérer l'utilisateur
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    
    # Créer les tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "client_id": str(user.client_id)}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "client_id": str(user.client_id)}
    )
    
    # Créer la session
    session = SessionModel(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        refresh_expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    # Mettre à jour last_login
    user.last_login = datetime.utcnow()
    
    db.add(session)
    db.commit()
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user={
            "id": str(user.id),
            "email": user.email,
            "nom": user.nom,
            "prenom": user.prenom,
            "role": user.role,
            "client_id": str(user.client_id)
        }
    )

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Déconnexion
    """
    # Révoquer toutes les sessions actives
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id,
        SessionModel.revoked == False
    ).all()
    
    for session in sessions:
        session.revoked = True
        session.revoked_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Déconnexion réussie"}

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Récupère les infos de l'utilisateur connecté
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "nom": current_user.nom,
        "prenom": current_user.prenom,
        "role": current_user.role,
        "client_id": str(current_user.client_id)
    }

# ==========================================