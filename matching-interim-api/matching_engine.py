# matching_engine_simple.py
# Version simplifiée mais fonctionnelle pour tester l'application

import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
import hashlib

class OptimizedInterimMatcher:
    """Version simplifiée du matcher pour tests"""
    
    def __init__(self, use_ai=False, client_id=None, client_folder=None):
        self.client_id = client_id or "default"
        self.client_folder = client_folder or f"data/{self.client_id}/"
        self.use_ai = False  # Désactivé pour cette version simple
        
        # Créer les dossiers
        for folder in [self.client_folder, f"{self.client_folder}cache/", 
                      f"{self.client_folder}exports/"]:
            os.makedirs(folder, exist_ok=True)
        
        self.candidats = None
        self.besoins = None
        self.missions_patterns = {}
        
        self.stats = {
            'cache_hits': 0,
            'api_calls': 0,
            'tokens_used': 0
        }
    
    def load_data(self, candidats_file, besoins_file):
        """Charge les données candidats et besoins"""
        print(f"📊 [{self.client_id}] Chargement des données...")
        
        try:
            # Chargement candidats
            if candidats_file.endswith('.csv'):
                self.candidats = pd.read_csv(candidats_file, encoding='utf-8-sig')
            else:
                self.candidats = pd.read_excel(candidats_file)
            
            # Chargement besoins
            if besoins_file.endswith('.csv'):
                self.besoins = pd.read_csv(besoins_file, encoding='utf-8-sig')
            else:
                self.besoins = pd.read_excel(besoins_file)
            
            print(f"✅ {len(self.candidats)} candidats chargés")
            print(f"✅ {len(self.besoins)} besoins chargés")
            
            # Analyse simplifiée des missions
            self.missions_patterns = {i: f"mission_{i}" for i in range(len(self.besoins))}
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur de chargement: {e}")
            return False
    
    def find_best_matches_optimized(self):
        """Matching simplifié"""
        if self.candidats is None or self.besoins is None:
            print("❌ Données non chargées")
            return None
        
        print(f"\n🚀 [{self.client_id}] MATCHING EN COURS...")
        resultats = []
        
        for idx, besoin in self.besoins.iterrows():
            print(f"📋 Traitement: {besoin.get('Poste_recherche', 'Poste')} - {besoin.get('Localisation', '')}")
            
            candidats_scores = []
            
            # Calcul simplifié des scores
            for _, candidat in self.candidats.iterrows():
                # Skip candidats non disponibles
                if str(candidat.get('Disponibilite', '')).lower() == 'en mission':
                    continue
                
                # Score aléatoire pour la démo (entre 40 et 95)
                score = np.random.randint(40, 95)
                
                candidats_scores.append({
                    'candidat_id': str(candidat.get('ID_Candidat', idx)),
                    'candidat_nom': f"{candidat.get('Prenom', '')} {candidat.get('Nom', '')}",
                    'score_total': score / 100,
                    'score_pct': score,
                    'telephone': candidat.get('Telephone', '06.XX.XX.XX.XX'),
                    'email': candidat.get('Email', 'email@example.com'),
                    'taux_min': candidat.get('Taux_horaire_min', 15),
                    'experience': candidat.get('Experience_annees', 1),
                    'disponibilite': candidat.get('Disponibilite', 'Immédiate')
                })
            
            # Tri par score
            candidats_scores.sort(key=lambda x: x['score_total'], reverse=True)
            top5 = candidats_scores[:5]
            
            resultats.append({
                'besoin': besoin,
                'top_candidats': top5,
                'explications': f"Matching simplifié pour {besoin.get('Poste_recherche', 'Poste')}"
            })
        
        print(f"✅ Matching terminé: {len(resultats)} postes traités")
        return resultats
    
    def export_results_optimized(self, resultats, output_file=None):
        """Export Excel simplifié"""
        if not resultats:
            print("❌ Aucun résultat à exporter")
            return None
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{self.client_folder}exports/matching_{self.client_id}_{timestamp}.xlsx"
        
        export_data = []
        
        for resultat in resultats:
            besoin = resultat['besoin']
            for i, candidat in enumerate(resultat['top_candidats'][:5], 1):
                export_data.append({
                    'Client': self.client_id,
                    'Poste': besoin.get('Poste_recherche', ''),
                    'Rang': i,
                    'Score': candidat['score_pct'],
                    'Candidat': candidat['candidat_nom'],
                    'Telephone': candidat['telephone']
                })
        
        df = pd.DataFrame(export_data)
        df.to_excel(output_file, index=False)
        
        print(f"✅ Résultats exportés: {output_file}")
        return df