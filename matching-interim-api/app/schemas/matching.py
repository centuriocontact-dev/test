# app/schemas/matching.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class MatchingRequest(BaseModel):
    """Requête pour lancer un matching"""
    besoin_id: Optional[uuid.UUID] = None  # Si None = tous les besoins
    use_ai: bool = False
    force_refresh: bool = False

class MatchingResponse(BaseModel):
    """Réponse d'un matching individuel"""
    id: str
    besoin_id: str
    candidat_id: str
    score_total: float
    score_competences: Optional[float]
    score_localisation: Optional[float]
    score_disponibilite: Optional[float]
    score_financier: Optional[float]
    score_experience: Optional[float]
    rang: Optional[int]
    points_forts: List[str]
    points_faibles: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MatchingResult(BaseModel):
    """Résultat global du matching"""
    success: bool
    message: str
    besoins_traites: int
    matchings_created: int
    export_file: Optional[str] = None

# ==========================================