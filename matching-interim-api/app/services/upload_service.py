# app/services/upload_service.py
from fastapi import UploadFile
from sqlalchemy.orm import Session
import pandas as pd
import os
from datetime import datetime
from typing import Tuple

from app.models.models import Candidat, Besoin
from app.config import settings

class UploadService:
    """Service de gestion des uploads"""
    
    async def save_upload_file(
        self,
        file: UploadFile,
        category: str,
        client_id: str
    ) -> str:
        """
        Sauvegarde un fichier uploadé
        
        Returns:
            str: Chemin du fichier sauvegardé
        """
        # Créer le dossier si nécessaire
        upload_dir = f"{settings.UPLOAD_DIR}/{category}/{client_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1]
        safe_filename = f"{category}_{timestamp}{file_ext}"
        
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Sauvegarder
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return file_path
    
    async def process_candidats_file(
        self,
        file_path: str,
        client_id: str,
        db: Session
    ) -> int:
        """
        Parse et insère les candidats en base
        
        Returns:
            int: Nombre de candidats insérés
        """
        # Lire le fichier
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        else:
            df = pd.read_excel(file_path)
        
        count = 0
        
        for _, row in df.iterrows():
            # Mapper les colonnes du fichier vers le modèle
            candidat = Candidat(
                id_externe=str(row.get('ID_Candidat', '')),
                nom=row.get('Nom', ''),
                prenom=row.get('Prenom', ''),
                email=row.get('Email'),
                telephone=row.get('Telephone'),
                code_postal=row.get('Code_postal'),
                ville=row.get('Ville'),
                departement=row.get('Departement'),
                metier_principal=row.get('Metier_principal'),
                experience_annees=row.get('Experience_annees'),
                disponibilite=row.get('Disponibilite', 'immediate'),
                taux_horaire_min=row.get('Taux_horaire_min'),
                competences=row.get('Competences', '').split(',') if row.get('Competences') else []
            )
            
            db.add(candidat)
            count += 1
        
        db.commit()
        return count
    
    async def process_besoins_file(
        self,
        file_path: str,
        client_id: str,
        db: Session
    ) -> int:
        """
        Parse et insère les besoins en base
        """
        df = pd.read_excel(file_path)
        
        count = 0
        
        for _, row in df.iterrows():
            besoin = Besoin(
                client_id=client_id,
                id_externe=str(row.get('ID_Besoin', '')),
                poste_recherche=row.get('Poste_recherche', ''),
                description=row.get('Description'),
                ville=row.get('Ville'),
                departement=row.get('Departement'),
                format_travail=row.get('Format_travail'),
                date_debut=pd.to_datetime(row.get('Date_debut')) if row.get('Date_debut') else None,
                taux_horaire_max=row.get('Taux_horaire_max'),
                experience_requise_min=row.get('Experience_requise_min'),
                competences_requises=row.get('Competences_requises', '').split(',') if row.get('Competences_requises') else []
            )
            
            db.add(besoin)
            count += 1
        
        db.commit()
        return count