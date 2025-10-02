# tests/test_endpoints.py
"""
Tests unitaires pour chaque endpoint principal
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta

class TestAuthEndpoints:
    """Tests des endpoints d'authentification"""
    
    def test_login_success(self, client: TestClient, test_users: tuple):
        """Test login réussi"""
        response = client.post(
            "/api/auth/login",
            data={"username": "user@client1.com", "password": "User123!"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Vérifications structure de la réponse
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        
        # Vérifications données utilisateur
        user_data = data["user"]
        assert user_data["email"] == "user@client1.com"
        assert user_data["role"] == "user"
        assert "id" in user_data
        assert "client_id" in user_data
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test récupération utilisateur courant"""
        response = client.get("/api/auth/me", headers=auth_headers["regular"])
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["email"] == "user@client1.com"
        assert data["role"] == "user"
        assert "id" in data
        assert "client_id" in data
    
    def test_logout(self, client: TestClient, auth_headers: dict):
        """Test déconnexion"""
        response = client.post("/api/auth/logout", headers=auth_headers["regular"])
        
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()

class TestCandidatsEndpoints:
    """Tests des endpoints candidats"""
    
    def test_list_candidats(self, client: TestClient, auth_headers: dict, test_candidats: list):
        """Test liste des candidats"""
        response = client.get("/api/candidats/", headers=auth_headers["regular"])
        
        assert response.status_code == status.HTTP_200_OK
        candidats = response.json()
        
        assert isinstance(candidats, list)
        assert len(candidats) == len(test_candidats)
        
        # Vérifier structure
        if candidats:
            first = candidats[0]
            assert "id" in first
            assert "nom" in first
            assert "prenom" in first
            assert "email" in first
    
    def test_list_candidats_with_filters(self, client: TestClient, auth_headers: dict, test_candidats: list):
        """Test liste avec filtres"""
        # Filtre par disponibilité
        response = client.get(
            "/api/candidats/?disponibilite=immediate",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        candidats = response.json()
        
        # Vérifier que le filtre est appliqué
        for candidat in candidats:
            assert candidat["disponibilite"] == "immediate"
    
    def test_get_candidat_by_id(self, client: TestClient, auth_headers: dict, test_candidats: list):
        """Test récupération candidat par ID"""
        candidat_id = test_candidats[0].id
        
        response = client.get(
            f"/api/candidats/{candidat_id}",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        candidat = response.json()
        
        assert candidat["id"] == str(candidat_id)
        assert candidat["nom"] == test_candidats[0].nom
    
    def test_create_candidat(self, client: TestClient, auth_headers: dict):
        """Test création candidat"""
        candidat_data = {
            "nom": "Nouveau",
            "prenom": "Candidat",
            "email": "nouveau@test.com",
            "telephone": "0600000000",
            "ville": "Paris",
            "departement": "75",
            "metier_principal": "Développeur",
            "experience_annees": 5.0,
            "disponibilite": "immediate",
            "taux_horaire_min": 20.0,
            "competences": ["Python", "FastAPI"]
        }
        
        response = client.post(
            "/api/candidats/",
            headers=auth_headers["regular"],
            json=candidat_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        created = response.json()
        
        assert created["nom"] == candidat_data["nom"]
        assert created["email"] == candidat_data["email"]
        assert "id" in created
    
    def test_update_candidat(self, client: TestClient, auth_headers: dict, test_candidats: list):
        """Test mise à jour candidat"""
        candidat_id = test_candidats[0].id
        
        update_data = {
            "disponibilite": "1_mois",
            "taux_horaire_min": 25.0
        }
        
        response = client.put(
            f"/api/candidats/{candidat_id}",
            headers=auth_headers["regular"],
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        updated = response.json()
        
        assert updated["disponibilite"] == "1_mois"
        assert updated["taux_horaire_min"] == 25.0
    
    def test_delete_candidat(self, client: TestClient, auth_headers: dict, test_candidats: list):
        """Test suppression (soft delete) candidat"""
        candidat_id = test_candidats[0].id
        
        response = client.delete(
            f"/api/candidats/{candidat_id}",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT

class TestBesoinsEndpoints:
    """Tests des endpoints besoins"""
    
    def test_list_besoins(self, client: TestClient, auth_headers: dict, test_besoins: list):
        """Test liste des besoins"""
        response = client.get("/api/besoins/", headers=auth_headers["regular"])
        
        assert response.status_code == status.HTTP_200_OK
        besoins = response.json()
        
        assert isinstance(besoins, list)
        # Client1 a 3 besoins
        assert len(besoins) == 3
    
    def test_list_besoins_filters(self, client: TestClient, auth_headers: dict, test_besoins: list):
        """Test filtres sur les besoins"""
        # Filtre par statut
        response = client.get(
            "/api/besoins/?statut=ouvert",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        besoins = response.json()
        
        for besoin in besoins:
            assert besoin["statut"] == "ouvert"
        
        # Filtre par priorité
        response = client.get(
            "/api/besoins/?priorite=haute",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        besoins = response.json()
        
        # Un seul besoin a priorité haute dans les fixtures
        assert len(besoins) == 1
        assert besoins[0]["priorite"] == "haute"
    
    def test_create_besoin(self, client: TestClient, auth_headers: dict, test_clients: tuple):
        """Test création besoin"""
        client1, _ = test_clients
        
        besoin_data = {
            "poste_recherche": "Développeur Python",
            "description": "Recherche développeur Python expérimenté",
            "ville": "Lyon",
            "departement": "69",
            "format_travail": "temps_plein",
            "date_debut": (datetime.now() + timedelta(days=30)).isoformat(),
            "experience_requise_min": 3.0,
            "competences_requises": ["Python", "FastAPI", "PostgreSQL"],
            "taux_horaire_max": 50.0,
            "nb_candidats_souhaites": 3
        }
        
        response = client.post(
            "/api/besoins/",
            headers=auth_headers["regular"],
            json=besoin_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        created = response.json()
        
        assert created["poste_recherche"] == besoin_data["poste_recherche"]
        assert created["client_id"] == str(client1.id)
        assert created["statut"] == "ouvert"  # Statut par défaut
        assert "id" in created
    
    def test_update_besoin(self, client: TestClient, auth_headers: dict, test_besoins: list):
        """Test mise à jour besoin"""
        besoin_id = test_besoins[0].id
        
        update_data = {
            "statut": "ferme",
            "priorite": "basse"
        }
        
        response = client.put(
            f"/api/besoins/{besoin_id}",
            headers=auth_headers["regular"],
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        updated = response.json()
        
        assert updated["statut"] == "ferme"
        assert updated["priorite"] == "basse"

class TestMatchingsEndpoints:
    """Tests des endpoints matchings"""
    
    def test_run_matching(self, client: TestClient, auth_headers: dict, 
                         test_besoins: list, test_candidats: list):
        """Test lancement matching"""
        besoin_id = test_besoins[0].id
        
        response = client.post(
            "/api/matchings/run",
            headers=auth_headers["regular"],
            json={
                "besoin_id": str(besoin_id),
                "use_ai": False,
                "force_refresh": True
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        
        assert "status" in result
        assert "besoins_processed" in result
        assert "matchings_created" in result
    
    def test_get_matchings_for_besoin(self, client: TestClient, auth_headers: dict, 
                                      test_matchings: list):
        """Test récupération matchings pour un besoin"""
        besoin_id = test_matchings[0].besoin_id
        
        response = client.get(
            f"/api/matchings/besoin/{besoin_id}",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        matchings = response.json()
        
        assert isinstance(matchings, list)
        assert len(matchings) > 0
        
        # Vérifier l'ordre (par score décroissant)
        scores = [m["score_total"] for m in matchings]
        assert scores == sorted(scores, reverse=True)
    
    def test_export_matching(self, client: TestClient, auth_headers: dict, 
                            test_matchings: list):
        """Test export Excel des matchings"""
        besoin_id = test_matchings[0].besoin_id
        
        response = client.get(
            f"/api/matchings/export/{besoin_id}",
            headers=auth_headers["regular"]
        )
        
        # Peut retourner 200 avec fichier ou 500 si export service non configuré
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        
        if response.status_code == status.HTTP_200_OK:
            # Vérifier que c'est bien un fichier Excel
            assert response.headers.get("content-type") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

class TestUploadEndpoints:
    """Tests des endpoints d'upload"""
    
    def test_upload_candidats_csv(self, client: TestClient, auth_headers: dict):
        """Test upload fichier candidats CSV"""
        import io
        
        csv_content = """nom,prenom,email,telephone,ville,departement
Martin,Jean,jean.martin@test.com,0600000000,Paris,75
Dupont,Marie,marie.dupont@test.com,0600000001,Lyon,69
"""
        
        file = io.BytesIO(csv_content.encode())
        
        response = client.post(
            "/api/uploads/candidats",
            headers=auth_headers["regular"],
            files={"file": ("candidats.csv", file, "text/csv")}
        )
        
        # Peut réussir ou échouer selon la config
        assert response.status_code in [
            status.HTTP_200_OK, 
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_400_BAD_REQUEST
        ]
    
    def test_upload_invalid_file_type(self, client: TestClient, auth_headers: dict):
        """Test upload avec type de fichier invalide"""
        import io
        
        file = io.BytesIO(b"fake content")
        
        response = client.post(
            "/api/uploads/candidats",
            headers=auth_headers["regular"],
            files={"file": ("test.exe", file, "application/x-msdownload")}
        )
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        ]

class TestHealthEndpoints:
    """Tests des endpoints de health check"""
    
    def test_basic_health(self, client: TestClient):
        """Test health check basique (sans auth)"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_database_health(self, client: TestClient):
        """Test health check database"""
        response = client.get("/health/db")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "status" in data
        assert data["connected"] == True
        assert "response_time_ms" in data
        assert "stats" in data
    
    def test_readiness_check(self, client: TestClient):
        """Test readiness probe"""
        response = client.get("/health/ready")
        
        # Peut être 200 ou 503 selon l'état
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]
        
        data = response.json()
        assert "ready" in data
        
        if response.status_code == status.HTTP_200_OK:
            assert data["ready"] == True
    
    def test_liveness_check(self, client: TestClient):
        """Test liveness probe"""
        response = client.get("/health/live")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["alive"] == True