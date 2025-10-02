# app/routers/besoins.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app.core.security import get_current_user
from app.core.dependencies import get_current_client_id
from app.models.models import User, Besoin
from app.schemas.besoin import BesoinCreate, BesoinUpdate, BesoinResponse

router = APIRouter()

@router.get("/", response_model=List[BesoinResponse])
def list_besoins(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    statut: Optional[str] = None,
    priorite: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Liste tous les besoins du client
    """
    query = db.query(Besoin).filter(Besoin.client_id == client_id)
    
    if statut:
        query = query.filter(Besoin.statut == statut)
    
    if priorite:
        query = query.filter(Besoin.priorite == priorite)
    
    besoins = query.order_by(Besoin.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        BesoinResponse(
            id=str(b.id),
            client_id=str(b.client_id),
            poste_recherche=b.poste_recherche,
            description=b.description,
            ville=b.ville,
            departement=b.departement,
            format_travail=b.format_travail,
            date_debut=b.date_debut,
            taux_horaire_max=b.taux_horaire_max,
            competences_requises=b.competences_requises or [],
            statut=b.statut,
            priorite=b.priorite,
            nb_matchings=b.nb_matchings,
            meilleur_score=b.meilleur_score,
            created_at=b.created_at
        )
        for b in besoins
    ]

@router.post("/", response_model=BesoinResponse, status_code=201)
def create_besoin(
    besoin: BesoinCreate,
    current_user: User = Depends(get_current_user),
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau besoin
    """
    # Forcer le client_id de l'utilisateur
    besoin_data = besoin.model_dump()
    besoin_data['client_id'] = client_id
    
    db_besoin = Besoin(**besoin_data)
    db.add(db_besoin)
    db.commit()
    db.refresh(db_besoin)
    
    return BesoinResponse(
        id=str(db_besoin.id),
        client_id=str(db_besoin.client_id),
        poste_recherche=db_besoin.poste_recherche,
        description=db_besoin.description,
        ville=db_besoin.ville,
        departement=db_besoin.departement,
        format_travail=db_besoin.format_travail,
        date_debut=db_besoin.date_debut,
        taux_horaire_max=db_besoin.taux_horaire_max,
        competences_requises=db_besoin.competences_requises or [],
        statut=db_besoin.statut,
        priorite=db_besoin.priorite,
        nb_matchings=db_besoin.nb_matchings,
        meilleur_score=db_besoin.meilleur_score,
        created_at=db_besoin.created_at
    )

@router.get("/{besoin_id}", response_model=BesoinResponse)
def get_besoin(
    besoin_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Récupère un besoin par ID
    """
    besoin = db.query(Besoin).filter(
        Besoin.id == besoin_id,
        Besoin.client_id == client_id
    ).first()
    
    if not besoin:
        raise HTTPException(status_code=404, detail="Besoin non trouvé")
    
    return BesoinResponse(
        id=str(besoin.id),
        client_id=str(besoin.client_id),
        poste_recherche=besoin.poste_recherche,
        description=besoin.description,
        ville=besoin.ville,
        departement=besoin.departement,
        format_travail=besoin.format_travail,
        date_debut=besoin.date_debut,
        taux_horaire_max=besoin.taux_horaire_max,
        competences_requises=besoin.competences_requises or [],
        statut=besoin.statut,
        priorite=besoin.priorite,
        nb_matchings=besoin.nb_matchings,
        meilleur_score=besoin.meilleur_score,
        created_at=besoin.created_at
    )

@router.put("/{besoin_id}", response_model=BesoinResponse)
def update_besoin(
    besoin_id: uuid.UUID,
    besoin_update: BesoinUpdate,
    current_user: User = Depends(get_current_user),
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Met à jour un besoin
    """
    besoin = db.query(Besoin).filter(
        Besoin.id == besoin_id,
        Besoin.client_id == client_id
    ).first()
    
    if not besoin:
        raise HTTPException(status_code=404, detail="Besoin non trouvé")
    
    # Mettre à jour
    update_data = besoin_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(besoin, field, value)
    
    db.commit()
    db.refresh(besoin)
    
    return BesoinResponse(
        id=str(besoin.id),
        client_id=str(besoin.client_id),
        poste_recherche=besoin.poste_recherche,
        description=besoin.description,
        ville=besoin.ville,
        departement=besoin.departement,
        format_travail=besoin.format_travail,
        date_debut=besoin.date_debut,
        taux_horaire_max=besoin.taux_horaire_max,
        competences_requises=besoin.competences_requises or [],
        statut=besoin.statut,
        priorite=besoin.priorite,
        nb_matchings=besoin.nb_matchings,
        meilleur_score=besoin.meilleur_score,
        created_at=besoin.created_at
    )