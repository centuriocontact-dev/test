# app/schemas/besoin.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class BesoinBase(BaseModel):
    poste_recherche: str
    description: Optional[str] = None
    ville: Optional[str] = None
    departement: Optional[str] = None
    format_travail: Optional[str] = None
    date_debut: Optional[date] = None
    taux_horaire_max: Optional[Decimal] = None
    competences_requises: List[str] = []

class BesoinCreate(BesoinBase):
    client_id: str

class BesoinUpdate(BaseModel):
    poste_recherche: Optional[str] = None
    description: Optional[str] = None
    statut: Optional[str] = None

class BesoinResponse(BesoinBase):
    id: str
    client_id: str
    statut: str
    priorite: str
    nb_matchings: int
    meilleur_score: Optional[Decimal]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==========================================