# tests/test_matching_engine.py
"""
Tests unitaires pour le moteur de matching
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from datetime import datetime

# Import du moteur à tester
from matching_engine import OptimizedInterimMatcher

class TestMatchingEngine:
    """Tests du moteur de matching"""
    
    @pytest.fixture
    def matcher(self):
        """Créer une instance du matcher pour les tests"""
        return OptimizedInterimMatcher(
            use_ai=False,
            client_id="test_client",
            client_folder="test_data/"
        )
    
    @pytest.fixture
    def sample_candidats_df(self):
        """DataFrame de candidats de test"""
        return pd.DataFrame({
            'ID_Candidat': ['C001', 'C002', 'C003', 'C004', 'C005'],
            'Nom': ['Martin', 'Dupont', 'Bernard', 'Petit', 'Robert'],
            'Prenom': ['Jean', 'Marie', 'Paul', 'Sophie', 'Pierre'],
            'Email': ['jean@test.com', 'marie@test.com', 'paul@test.com', 'sophie@test.com', 'pierre@test.com'],
            'Telephone': ['0600000001', '0600000002', '0600000003', '0600000004', '0600000005'],
            'Disponibilite': ['Immédiate', 'Immédiate', 'En mission', '1 semaine', 'Immédiate'],
            'Experience_annees': [5, 3, 7, 2, 10],
            'Taux_horaire_min': [20, 18, 25, 15, 30],
            'Competences': ['Python,SQL', 'Java,Spring', 'Python,Django', 'JavaScript,React', 'Python,FastAPI'],
            'Ville': ['Paris', 'Lyon', 'Paris', 'Marseille', 'Paris'],
            'Departement': ['75', '69', '75', '13', '75']
        })
    
    @pytest.fixture
    def sample_besoins_df(self):
        """DataFrame de besoins de test"""
        return pd.DataFrame({
            'ID_Besoin': ['B001', 'B002'],
            'Poste_recherche': ['Développeur Python', 'Développeur Java'],
            'Localisation': ['Paris', 'Lyon'],
            'Departement': ['75', '69'],
            'Experience_min': [3, 2],
            'Taux_horaire_max': [50, 45],
            'Competences_requises': ['Python', 'Java'],
            'Date_debut': [datetime.now(), datetime.now()],
            'Priorite': ['haute', 'normale']
        })
    
    def test_init_creates_folders(self):
        """Test que l'initialisation crée les dossiers nécessaires"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client_folder = f"{tmpdir}/test_client/"
            matcher = OptimizedInterimMatcher(
                client_id="test",
                client_folder=client_folder
            )
            
            # Vérifier que les dossiers sont créés
            assert os.path.exists(client_folder)
            assert os.path.exists(f"{client_folder}cache/")
            assert os.path.exists(f"{client_folder}exports/")
    
    def test_load_data_csv(self, matcher, sample_candidats_df, sample_besoins_df):
        """Test chargement de données CSV"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Sauvegarder les DataFrames en CSV
            candidats_file = f"{tmpdir}/candidats.csv"
            besoins_file = f"{tmpdir}/besoins.csv"
            
            sample_candidats_df.to_csv(candidats_file, index=False)
            sample_besoins_df.to_csv(besoins_file, index=False)
            
            # Charger les données
            result = matcher.load_data(candidats_file, besoins_file)
            
            assert result == True
            assert matcher.candidats is not None
            assert matcher.besoins is not None
            assert len(matcher.candidats) == 5
            assert len(matcher.besoins) == 2
    
    def test_load_data_excel(self, matcher, sample_candidats_df, sample_besoins_df):
        """Test chargement de données Excel"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Sauvegarder en Excel
            candidats_file = f"{tmpdir}/candidats.xlsx"
            besoins_file = f"{tmpdir}/besoins.xlsx"
            
            sample_candidats_df.to_excel(candidats_file, index=False)
            sample_besoins_df.to_excel(besoins_file, index=False)
            
            # Charger les données
            result = matcher.load_data(candidats_file, besoins_file)
            
            assert result == True
            assert len(matcher.candidats) == 5
            assert len(matcher.besoins) == 2
    
    def test_load_data_invalid_file(self, matcher):
        """Test chargement avec fichier invalide"""
        result = matcher.load_data("nonexistent.csv", "nonexistent.csv")
        assert result == False
    
    def test_find_matches_without_data(self, matcher):
        """Test matching sans données chargées"""
        result = matcher.find_best_matches_optimized()
        assert result is None
    
    def test_find_matches_filters_unavailable(self, matcher, sample_candidats_df, sample_besoins_df):
        """Test que le matching filtre les candidats non disponibles"""
        # Configurer les données
        matcher.candidats = sample_candidats_df
        matcher.besoins = sample_besoins_df
        
        # Exécuter le matching
        results = matcher.find_best_matches_optimized()
        
        assert results is not None
        assert len(results) == 2  # 2 besoins
        
        # Vérifier qu'aucun candidat "En mission" n'est dans les résultats
        for resultat in results:
            for candidat in resultat['top_candidats']:
                # Le candidat C003 est "En mission" et ne doit pas apparaître
                assert candidat['candidat_id'] != 'C003'
    
    def test_find_matches_returns_top5(self, matcher, sample_candidats_df, sample_besoins_df):
        """Test que le matching retourne bien le top 5"""
        matcher.candidats = sample_candidats_df
        matcher.besoins = sample_besoins_df
        
        results = matcher.find_best_matches_optimized()
        
        for resultat in results:
            # Maximum 5 candidats par besoin
            assert len(resultat['top_candidats']) <= 5
            
            # Vérifier que les candidats sont triés par score
            scores = [c['score_total'] for c in resultat['top_candidats']]
            assert scores == sorted(scores, reverse=True)
    
    def test_find_matches_score_range(self, matcher, sample_candidats_df, sample_besoins_df):
        """Test que les scores sont dans la bonne plage"""
        matcher.candidats = sample_candidats_df
        matcher.besoins = sample_besoins_df
        
        results = matcher.find_best_matches_optimized()
        
        for resultat in results:
            for candidat in resultat['top_candidats']:
                # Score total entre 0 et 1
                assert 0 <= candidat['score_total'] <= 1
                # Score en pourcentage entre 0 et 100
                assert 0 <= candidat['score_pct'] <= 100
    
    def test_export_results_creates_file(self, matcher, sample_candidats_df, sample_besoins_df):
        """Test que l'export crée bien un fichier Excel"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matcher.client_folder = f"{tmpdir}/"
            os.makedirs(f"{tmpdir}/exports/", exist_ok=True)
            
            matcher.candidats = sample_candidats_df
            matcher.besoins = sample_besoins_df
            
            # Exécuter le matching
            results = matcher.find_best_matches_optimized()
            
            # Exporter
            output_file = f"{tmpdir}/test_export.xlsx"
            df = matcher.export_results_optimized(results, output_file)
            
            assert df is not None
            assert os.path.exists(output_file)
            
            # Vérifier le contenu du DataFrame exporté
            assert 'Client' in df.columns
            assert 'Poste' in df.columns
            assert 'Rang' in df.columns
            assert 'Score' in df.columns
            assert 'Candidat' in df.columns
    
    def test_export_without_results(self, matcher):
        """Test export sans résultats"""
        result = matcher.export_results_optimized([])
        assert result is None
    
    def test_matching_with_empty_candidats(self, matcher, sample_besoins_df):
        """Test matching avec liste de candidats vide"""
        matcher.candidats = pd.DataFrame()
        matcher.besoins = sample_besoins_df
        
        results = matcher.find_best_matches_optimized()
        
        assert results is not None
        # Chaque besoin devrait avoir une liste vide de candidats
        for resultat in results:
            assert resultat['top_candidats'] == []
    
    def test_matching_preserves_candidat_info(self, matcher, sample_candidats_df, sample_besoins_df):
        """Test que le matching préserve toutes les infos candidat"""
        matcher.candidats = sample_candidats_df
        matcher.besoins = sample_besoins_df
        
        results = matcher.find_best_matches_optimized()
        
        for resultat in results:
            for candidat in resultat['top_candidats']:
                # Vérifier que toutes les infos requises sont présentes
                assert 'candidat_id' in candidat
                assert 'candidat_nom' in candidat
                assert 'score_total' in candidat
                assert 'score_pct' in candidat
                assert 'telephone' in candidat
                assert 'email' in candidat
                assert 'taux_min' in candidat
                assert 'experience' in candidat
                assert 'disponibilite' in candidat
    
    def test_client_id_consistency(self, matcher):
        """Test que le client_id est utilisé partout"""
        assert matcher.client_id == "test_client"
        assert "test_client" in matcher.client_folder
    
    def test_stats_tracking(self, matcher):
        """Test que les statistiques sont trackées"""
        assert 'cache_hits' in matcher.stats
        assert 'api_calls' in matcher.stats
        assert 'tokens_used' in matcher.stats
        
        # Valeurs initiales
        assert matcher.stats['cache_hits'] == 0
        assert matcher.stats['api_calls'] == 0
        assert matcher.stats['tokens_used'] == 0

class TestMatchingEnginePerformance:
    """Tests de performance du moteur"""
    
    def test_large_dataset_performance(self):
        """Test avec un grand dataset"""
        # Créer un grand dataset
        n_candidats = 1000
        n_besoins = 50
        
        candidats_df = pd.DataFrame({
            'ID_Candidat': [f'C{i:04d}' for i in range(n_candidats)],
            'Nom': [f'Nom{i}' for i in range(n_candidats)],
            'Prenom': [f'Prenom{i}' for i in range(n_candidats)],
            'Email': [f'test{i}@test.com' for i in range(n_candidats)],
            'Telephone': [f'06{i:08d}' for i in range(n_candidats)],
            'Disponibilite': np.random.choice(['Immédiate', 'En mission', '1 semaine'], n_candidats),
            'Experience_annees': np.random.randint(1, 20, n_candidats),
            'Taux_horaire_min': np.random.randint(15, 50, n_candidats)
        })
        
        besoins_df = pd.DataFrame({
            'ID_Besoin': [f'B{i:03d}' for i in range(n_besoins)],
            'Poste_recherche': [f'Poste {i}' for i in range(n_besoins)],
            'Localisation': np.random.choice(['Paris', 'Lyon', 'Marseille'], n_besoins)
        })
        
        matcher = OptimizedInterimMatcher(use_ai=False)
        matcher.candidats = candidats_df
        matcher.besoins = besoins_df
        
        # Mesurer le temps
        import time
        start = time.time()
        results = matcher.find_best_matches_optimized()
        duration = time.time() - start
        
        assert results is not None
        assert len(results) == n_besoins
        
        # Performance check: doit finir en moins de 10 secondes
        assert duration < 10, f"Matching trop lent: {duration:.2f}s pour {n_candidats} candidats et {n_besoins} besoins"
        
        print(f"Performance: {duration:.2f}s pour {n_candidats} candidats et {n_besoins} besoins")

class TestMatchingEngineEdgeCases:
    """Tests des cas limites"""
    
    def test_special_characters_in_names(self):
        """Test avec caractères spéciaux dans les noms"""
        candidats_df = pd.DataFrame({
            'ID_Candidat': ['C001'],
            'Nom': ["O'Brien-Müller"],
            'Prenom': ['José-María'],
            'Email': ['test@test.com'],
            'Telephone': ['0600000000'],
            'Disponibilite': ['Immédiate'],
            'Experience_annees': [5],
            'Taux_horaire_min': [20]
        })
        
        besoins_df = pd.DataFrame({
            'ID_Besoin': ['B001'],
            'Poste_recherche': ['Développeur'],
            'Localisation': ['Paris']
        })
        
        matcher = OptimizedInterimMatcher(use_ai=False)
        matcher.candidats = candidats_df
        matcher.besoins = besoins_df
        
        results = matcher.find_best_matches_optimized()
        
        assert results is not None
        assert len(results[0]['top_candidats']) == 1
        assert "O'Brien-Müller" in results[0]['top_candidats'][0]['candidat_nom']
    
    def test_null_values_handling(self):
        """Test gestion des valeurs nulles"""
        candidats_df = pd.DataFrame({
            'ID_Candidat': ['C001', 'C002'],
            'Nom': ['Martin', None],
            'Prenom': [None, 'Marie'],
            'Email': [None, 'marie@test.com'],
            'Telephone': ['0600000000', None],
            'Disponibilite': ['Immédiate', None],
            'Experience_annees': [5, None],
            'Taux_horaire_min': [None, 20]
        })
        
        besoins_df = pd.DataFrame({
            'ID_Besoin': ['B001'],
            'Poste_recherche': ['Test'],
            'Localisation': ['Paris']
        })
        
        matcher = OptimizedInterimMatcher(use_ai=False)
        matcher.candidats = candidats_df
        matcher.besoins = besoins_df
        
        # Ne doit pas crasher
        results = matcher.find_best_matches_optimized()
        assert results is not None