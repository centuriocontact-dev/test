# app/services/export_service.py
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.models.models import Besoin, Matching, Candidat

class ExportService:
    """Service d'export des résultats"""
    
    async def export_matching_to_excel(
        self,
        besoin_id: str,
        client_id: str,
        db: Session
    ) -> str:
        """
        Exporte les résultats de matching en Excel
        """
        # Récupérer le besoin
        besoin = db.query(Besoin).filter(Besoin.id == besoin_id).first()
        if not besoin:
            raise Exception("Besoin non trouvé")
        
        # Récupérer les matchings
        matchings = db.query(Matching).filter(
            Matching.besoin_id == besoin_id
        ).order_by(Matching.score_total.desc()).all()
        
        # Préparer les données
        data = []
        for matching in matchings:
            candidat = db.query(Candidat).filter(
                Candidat.id == matching.candidat_id
            ).first()
            
            if candidat:
                data.append({
                    'Rang': matching.rang,
                    'Score': f"{float(matching.score_total):.1f}%",
                    'Candidat': f"{candidat.prenom} {candidat.nom}",
                    'Email': candidat.email,
                    'Téléphone': candidat.telephone,
                    'Localisation': f"{candidat.ville} ({candidat.departement})",
                    'Expérience': f"{float(candidat.experience_annees):.1f} ans" if candidat.experience_annees else "N/A",
                    'Disponibilité': candidat.disponibilite,
                    'Taux horaire min': f"{float(candidat.taux_horaire_min):.2f}€" if candidat.taux_horaire_min else "N/A"
                })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Créer le dossier d'export
        export_dir = f"data/{client_id}/exports"
        os.makedirs(export_dir, exist_ok=True)
        
        # Nom du fichier
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{export_dir}/matching_{besoin.poste_recherche.replace(' ', '_')}_{timestamp}.xlsx"
        
        # Exporter
        df.to_excel(filename, index=False, sheet_name="Matching")
        
        return filename