# app/schemas/candidat.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class CandidatBase(BaseModel):
    nom: str
    prenom: str
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    departement: Optional[str] = None
    metier_principal: Optional[str] = None
    experience_annees: Optional[Decimal] = None
    disponibilite: str = "immediate"
    taux_horaire_min: Optional[Decimal] = None
    competences: List[str] = []

class CandidatCreate(CandidatBase):
    pass

class CandidatUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[EmailStr] = None
    disponibilite: Optional[str] = None
    competences: Optional[List[str]] = None

class CandidatResponse(CandidatBase):
    id: str
    score_completude: int
    actif: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==========================================