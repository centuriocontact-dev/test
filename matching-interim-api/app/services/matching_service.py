# app/services/matching_service.py
import os
import sys
from sqlalchemy.orm import Session
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime

# Import du moteur existant (SANS MODIFICATION)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from matching_engine import OptimizedInterimMatcher

from app.models.models import Besoin, Candidat, Matching, Client
from app.schemas.matching import MatchingResult

class MatchingService:
    """
    Service qui intègre le matching_engine.py existant
    sans le modifier
    """
    
    async def run_matching(
        self,
        client_id: str,
        besoin_id: Optional[str] = None,
        use_ai: bool = False,
        force_refresh: bool = False,
        db: Session = None
    ) -> MatchingResult:
        """
        Lance le matching en utilisant le moteur existant
        """
        # Récupérer le client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise Exception("Client non trouvé")
        
        client_folder = f"data/{client.code}/"
        
        # Préparer les fichiers CSV temporaires
        candidats_file = await self._export_candidats_to_csv(client_id, db)
        besoins_file = await self._export_besoins_to_csv(client_id, besoin_id, db)
        
        # Initialiser le matcher (votre code existant)
        matcher = OptimizedInterimMatcher(
            use_ai=use_ai,
            client_id=client.code,
            client_folder=client_folder
        )
        
        # Charger les données
        success = matcher.load_data(candidats_file, besoins_file)
        
        if not success:
            raise Exception("Erreur lors du chargement des données")
        
        # Lancer le matching
        results = matcher.find_best_matches_optimized()
        
        if not results:
            raise Exception("Aucun résultat de matching")
        
        # Sauvegarder les résultats en base
        matchings_created = await self._save_results_to_db(
            results,
            client_id,
            db,
            force_refresh
        )
        
        # Export Excel
        export_file = matcher.export_results_optimized(results)
        
        return MatchingResult(
            success=True,
            message=f"Matching terminé avec succès",
            besoins_traites=len(results),
            matchings_created=matchings_created,
            export_file=str(export_file) if export_file is not None else None
        )
    
    async def _export_candidats_to_csv(
        self,
        client_id: str,
        db: Session
    ) -> str:
        """
        Exporte les candidats actifs en CSV pour le matcher
        """
        candidats = db.query(Candidat).filter(
            Candidat.actif == True
        ).all()
        
        # Convertir en DataFrame
        data = []
        for c in candidats:
            data.append({
                'ID_Candidat': str(c.id),
                'Nom': c.nom,
                'Prenom': c.prenom,
                'Email': c.email,
                'Telephone': c.telephone,
                'Code_postal': c.code_postal,
                'Ville': c.ville,
                'Departement': c.departement,
                'Metier_principal': c.metier_principal,
                'Experience_annees': float(c.experience_annees) if c.experience_annees else 0,
                'Disponibilite': c.disponibilite,
                'Taux_horaire_min': float(c.taux_horaire_min) if c.taux_horaire_min else 0,
                'Competences': ','.join(c.competences) if c.competences else ''
            })
        
        df = pd.DataFrame(data)
        
        # Sauvegarder
        temp_file = f"uploads/temp_candidats_{client_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        df.to_csv(temp_file, index=False, encoding='utf-8-sig')
        
        return temp_file
    
    async def _export_besoins_to_csv(
        self,
        client_id: str,
        besoin_id: Optional[str],
        db: Session
    ) -> str:
        """
        Exporte les besoins en Excel pour le matcher
        """
        query = db.query(Besoin).filter(
            Besoin.client_id == client_id,
            Besoin.statut == 'ouvert'
        )
        
        if besoin_id:
            query = query.filter(Besoin.id == besoin_id)
        
        besoins = query.all()
        
        # Convertir en DataFrame
        data = []
        for b in besoins:
            data.append({
                'ID_Besoin': str(b.id),
                'Poste_recherche': b.poste_recherche,
                'Description': b.description,
                'Localisation': b.ville,
                'Departement': b.departement,
                'Format_travail': b.format_travail,
                'Date_debut': b.date_debut,
                'Taux_horaire_max': float(b.taux_horaire_max) if b.taux_horaire_max else 0,
                'Experience_requise_min': float(b.experience_requise_min) if b.experience_requise_min else 0,
                'Competences_requises': ','.join(b.competences_requises) if b.competences_requises else ''
            })
        
        df = pd.DataFrame(data)
        
        # Sauvegarder
        temp_file = f"uploads/temp_besoins_{client_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        df.to_excel(temp_file, index=False)
        
        return temp_file
    
    async def _save_results_to_db(
        self,
        results: List[Dict],
        client_id: str,
        db: Session,
        force_refresh: bool = False
    ) -> int:
        """
        Sauvegarde les résultats du matching en base
        """
        matchings_created = 0
        
        for resultat in results:
            besoin = resultat['besoin']
            besoin_id = besoin.get('ID_Besoin')
            
            # Supprimer les anciens matchings si force_refresh
            if force_refresh:
                db.query(Matching).filter(
                    Matching.besoin_id == besoin_id
                ).delete()
            
            # Créer les nouveaux matchings
            for i, candidat in enumerate(resultat['top_candidats'], 1):
                matching = Matching(
                    besoin_id=besoin_id,
                    candidat_id=candidat['candidat_id'],
                    client_id=client_id,
                    score_total=candidat['score_total'] * 100,  # Convertir en pourcentage
                    rang=i,
                    points_forts=[],
                    points_faibles=[],
                    explications={}
                )
                
                db.add(matching)
                matchings_created += 1
            
            # Mettre à jour le besoin
            besoin_obj = db.query(Besoin).filter(Besoin.id == besoin_id).first()
            if besoin_obj:
                besoin_obj.nb_matchings = len(resultat['top_candidats'])
                besoin_obj.meilleur_score = resultat['top_candidats'][0]['score_pct'] if resultat['top_candidats'] else None
                besoin_obj.derniere_analyse = datetime.utcnow()
        
        db.commit()
        
        return matchings_created