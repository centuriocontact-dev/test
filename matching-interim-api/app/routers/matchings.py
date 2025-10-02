# app/routers/matchings.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import get_db
from app.core.security import get_current_user
from app.core.dependencies import get_current_client_id
from app.models.models import User, Besoin, Matching
from app.schemas.matching import MatchingRequest, MatchingResponse, MatchingResult
from app.services.matching_service import MatchingService

router = APIRouter()
matching_service = MatchingService()

@router.post("/run", response_model=MatchingResult)
async def run_matching(
    request: MatchingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Lance un matching pour un ou tous les besoins
    
    - **besoin_id**: ID du besoin spécifique (optionnel, si vide = tous les besoins)
    - **use_ai**: Utiliser l'IA GPT (optionnel)
    - **force_refresh**: Forcer le recalcul (ignore le cache)
    """
    try:
        # Vérifier les permissions
        if request.besoin_id:
            besoin = db.query(Besoin).filter(
                Besoin.id == request.besoin_id,
                Besoin.client_id == client_id
            ).first()
            
            if not besoin:
                raise HTTPException(
                    status_code=404,
                    detail="Besoin non trouvé ou accès non autorisé"
                )
        
        # Lancer le matching (synchrone pour l'instant)
        result = await matching_service.run_matching(
            client_id=client_id,
            besoin_id=str(request.besoin_id) if request.besoin_id else None,
            use_ai=request.use_ai,
            force_refresh=request.force_refresh,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du matching: {str(e)}"
        )

@router.get("/besoin/{besoin_id}", response_model=List[MatchingResponse])
def get_matchings_for_besoin(
    besoin_id: uuid.UUID,
    limit: int = 20,
    min_score: float = 0,
    current_user: User = Depends(get_current_user),
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Récupère les matchings pour un besoin donné
    """
    # Vérifier le besoin et permissions
    besoin = db.query(Besoin).filter(
        Besoin.id == besoin_id,
        Besoin.client_id == client_id
    ).first()
    
    if not besoin:
        raise HTTPException(
            status_code=404,
            detail="Besoin non trouvé"
        )
    
    # Récupérer les matchings
    matchings = db.query(Matching).filter(
        Matching.besoin_id == besoin_id,
        Matching.score_total >= min_score
    ).order_by(Matching.score_total.desc()).limit(limit).all()
    
    return [
        MatchingResponse(
            id=str(m.id),
            besoin_id=str(m.besoin_id),
            candidat_id=str(m.candidat_id),
            score_total=float(m.score_total),
            score_competences=float(m.score_competences) if m.score_competences else None,
            score_localisation=float(m.score_localisation) if m.score_localisation else None,
            score_disponibilite=float(m.score_disponibilite) if m.score_disponibilite else None,
            score_financier=float(m.score_financier) if m.score_financier else None,
            score_experience=float(m.score_experience) if m.score_experience else None,
            rang=m.rang,
            points_forts=m.points_forts or [],
            points_faibles=m.points_faibles or [],
            created_at=m.created_at
        )
        for m in matchings
    ]

@router.get("/export/{besoin_id}")
async def export_matching_results(
    besoin_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Exporte les résultats de matching en Excel
    """
    from app.services.export_service import ExportService
    
    export_service = ExportService()
    
    try:
        file_path = await export_service.export_matching_to_excel(
            besoin_id=str(besoin_id),
            client_id=client_id,
            db=db
        )
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=f"matching_{besoin_id}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'export: {str(e)}"
        )

# ==========================================