# app/routers/uploads.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
from datetime import datetime

from app.database import get_db
from app.core.security import get_current_user
from app.core.dependencies import get_current_client_id
from app.models.models import User
from app.services.upload_service import UploadService
from app.config import settings

router = APIRouter()
upload_service = UploadService()

@router.post("/candidats")
async def upload_candidats(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Upload fichier candidats (CSV ou Excel)
    """
    # Vérifier l'extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non autorisée. Formats acceptés: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Sauvegarder le fichier
    try:
        saved_path = await upload_service.save_upload_file(
            file,
            "candidats",
            client_id
        )
        
        # Parser et insérer en base
        candidats_count = await upload_service.process_candidats_file(
            saved_path,
            client_id,
            db
        )
        
        return {
            "message": "Fichier candidats uploadé avec succès",
            "filename": file.filename,
            "path": saved_path,
            "candidats_imported": candidats_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'upload: {str(e)}"
        )

@router.post("/besoins")
async def upload_besoins(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Upload fichier besoins (Excel)
    """
    # Vérifier l'extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Seuls les fichiers Excel sont acceptés pour les besoins"
        )
    
    try:
        saved_path = await upload_service.save_upload_file(
            file,
            "besoins",
            client_id
        )
        
        # Parser et insérer en base
        besoins_count = await upload_service.process_besoins_file(
            saved_path,
            client_id,
            db
        )
        
        return {
            "message": "Fichier besoins uploadé avec succès",
            "filename": file.filename,
            "path": saved_path,
            "besoins_imported": besoins_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'upload: {str(e)}"
        )

# ==========================================