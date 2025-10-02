# app/routers/candidats.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Candidat
from app.schemas.candidat import CandidatCreate, CandidatUpdate, CandidatResponse

router = APIRouter()

@router.get("/", response_model=List[CandidatResponse])
def list_candidats(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    disponibilite: Optional[str] = None,
    departement: Optional[str] = None,
    actif_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Liste tous les candidats avec filtres
    """
    query = db.query(Candidat)
    
    # Filtres
    if actif_only:
        query = query.filter(Candidat.actif == True)
    
    if disponibilite:
        query = query.filter(Candidat.disponibilite == disponibilite)
    
    if departement:
        query = query.filter(Candidat.departement == departement)
    
    if search:
        query = query.filter(
            (Candidat.nom.ilike(f"%{search}%")) |
            (Candidat.prenom.ilike(f"%{search}%")) |
            (Candidat.email.ilike(f"%{search}%"))
        )
    
    candidats = query.order_by(Candidat.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        CandidatResponse(
            id=str(c.id),
            nom=c.nom,
            prenom=c.prenom,
            email=c.email,
            telephone=c.telephone,
            code_postal=c.code_postal,
            ville=c.ville,
            departement=c.departement,
            metier_principal=c.metier_principal,
            experience_annees=c.experience_annees,
            disponibilite=c.disponibilite,
            taux_horaire_min=c.taux_horaire_min,
            competences=c.competences or [],
            score_completude=c.score_completude,
            actif=c.actif,
            created_at=c.created_at
        )
        for c in candidats
    ]

@router.post("/", response_model=CandidatResponse, status_code=201)
def create_candidat(
    candidat: CandidatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau candidat
    """
    # Vérifier si email existe
    if candidat.email:
        existing = db.query(Candidat).filter(Candidat.email == candidat.email).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Un candidat avec cet email existe déjà"
            )
    
    # Créer le candidat
    db_candidat = Candidat(**candidat.model_dump())
    db.add(db_candidat)
    db.commit()
    db.refresh(db_candidat)
    
    return CandidatResponse(
        id=str(db_candidat.id),
        nom=db_candidat.nom,
        prenom=db_candidat.prenom,
        email=db_candidat.email,
        telephone=db_candidat.telephone,
        code_postal=db_candidat.code_postal,
        ville=db_candidat.ville,
        departement=db_candidat.departement,
        metier_principal=db_candidat.metier_principal,
        experience_annees=db_candidat.experience_annees,
        disponibilite=db_candidat.disponibilite,
        taux_horaire_min=db_candidat.taux_horaire_min,
        competences=db_candidat.competences or [],
        score_completude=db_candidat.score_completude,
        actif=db_candidat.actif,
        created_at=db_candidat.created_at
    )

@router.get("/{candidat_id}", response_model=CandidatResponse)
def get_candidat(
    candidat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère un candidat par ID
    """
    candidat = db.query(Candidat).filter(Candidat.id == candidat_id).first()
    
    if not candidat:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    
    return CandidatResponse(
        id=str(candidat.id),
        nom=candidat.nom,
        prenom=candidat.prenom,
        email=candidat.email,
        telephone=candidat.telephone,
        code_postal=candidat.code_postal,
        ville=candidat.ville,
        departement=candidat.departement,
        metier_principal=candidat.metier_principal,
        experience_annees=candidat.experience_annees,
        disponibilite=candidat.disponibilite,
        taux_horaire_min=candidat.taux_horaire_min,
        competences=candidat.competences or [],
        score_completude=candidat.score_completude,
        actif=candidat.actif,
        created_at=candidat.created_at
    )

@router.put("/{candidat_id}", response_model=CandidatResponse)
def update_candidat(
    candidat_id: uuid.UUID,
    candidat_update: CandidatUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour un candidat
    """
    candidat = db.query(Candidat).filter(Candidat.id == candidat_id).first()
    
    if not candidat:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    
    # Mettre à jour
    update_data = candidat_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(candidat, field, value)
    
    db.commit()
    db.refresh(candidat)
    
    return CandidatResponse(
        id=str(candidat.id),
        nom=candidat.nom,
        prenom=candidat.prenom,
        email=candidat.email,
        telephone=candidat.telephone,
        code_postal=candidat.code_postal,
        ville=candidat.ville,
        departement=candidat.departement,
        metier_principal=candidat.metier_principal,
        experience_annees=candidat.experience_annees,
        disponibilite=candidat.disponibilite,
        taux_horaire_min=candidat.taux_horaire_min,
        competences=candidat.competences or [],
        score_completude=candidat.score_completude,
        actif=candidat.actif,
        created_at=candidat.created_at
    )

@router.delete("/{candidat_id}", status_code=204)
def delete_candidat(
    candidat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime (désactive) un candidat
    """
    candidat = db.query(Candidat).filter(Candidat.id == candidat_id).first()
    
    if not candidat:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    
    # Soft delete
    candidat.actif = False
    db.commit()

# ==========================================