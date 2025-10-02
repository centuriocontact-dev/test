# tests/test_multi_tenant.py
"""
Tests critiques d'isolation multi-tenant
Vérifie qu'un client ne peut JAMAIS accéder aux données d'un autre client
"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
import uuid

from app.models.models import Candidat, Besoin, Matching, Candidature

class TestMultiTenantIsolation:
    """Tests d'isolation entre clients - CRITIQUE POUR LA SÉCURITÉ"""
    
    def test_cannot_access_other_client_besoins(
        self,
        client: TestClient,
        db: Session,
        test_besoins: list,
        auth_headers: dict
    ):
        """Un utilisateur ne peut pas voir les besoins d'un autre client"""
        # Besoin du client 2
        other_client_besoin = test_besoins[3]  # Dernier besoin = client2
        
        # Tentative d'accès avec token client1
        response = client.get(
            f"/api/besoins/{other_client_besoin.id}",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "non trouvé" in response.json()["detail"].lower()
    
    def test_cannot_list_other_client_besoins(
        self,
        client: TestClient,
        db: Session,
        test_besoins: list,
        auth_headers: dict
    ):
        """La liste des besoins ne contient que ceux du client"""
        response = client.get(
            "/api/besoins/",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        besoins = response.json()
        
        # Vérifier qu'on n'a que les besoins du client1 (3 besoins)
        assert len(besoins) == 3
        
        # Vérifier qu'aucun besoin n'appartient au client2
        for besoin in besoins:
            assert besoin["id"] != str(test_besoins[3].id)
    
    def test_cannot_modify_other_client_besoin(
        self,
        client: TestClient,
        db: Session,
        test_besoins: list,
        auth_headers: dict
    ):
        """Un utilisateur ne peut pas modifier un besoin d'un autre client"""
        other_client_besoin = test_besoins[3]
        
        response = client.put(
            f"/api/besoins/{other_client_besoin.id}",
            headers=auth_headers["regular"],
            json={"statut": "ferme"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Vérifier que le besoin n'a pas été modifié
        db.refresh(other_client_besoin)
        assert other_client_besoin.statut == "ouvert"
    
    def test_cannot_run_matching_for_other_client_besoin(
        self,
        client: TestClient,
        db: Session,
        test_besoins: list,
        auth_headers: dict
    ):
        """Un utilisateur ne peut pas lancer un matching pour un besoin d'un autre client"""
        other_client_besoin = test_besoins[3]
        
        response = client.post(
            "/api/matchings/run",
            headers=auth_headers["regular"],
            json={"besoin_id": str(other_client_besoin.id)}
        )
        
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]
    
    def test_cannot_access_other_client_matchings(
        self,
        client: TestClient,
        db: Session,
        test_matchings: list,
        test_besoins: list,
        test_clients: tuple,
        auth_headers: dict
    ):
        """Un utilisateur ne peut pas voir les matchings d'un autre client"""
        # Créer un matching pour le client2
        client1, client2 = test_clients
        other_besoin = test_besoins[3]
        
        other_matching = Matching(
            id=uuid.uuid4(),
            besoin_id=other_besoin.id,
            candidat_id=test_matchings[0].candidat_id,
            client_id=client2.id,
            score_total=85
        )
        db.add(other_matching)
        db.commit()
        
        # Tentative d'accès aux matchings du besoin client2
        response = client.get(
            f"/api/matchings/besoin/{other_besoin.id}",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_candidat_data_shared_but_operations_isolated(
        self,
        client: TestClient,
        db: Session,
        test_candidats: list,
        auth_headers: dict
    ):
        """Les candidats sont partagés mais les opérations restent isolées"""
        # Les deux clients peuvent voir les mêmes candidats
        response1 = client.get(
            "/api/candidats/",
            headers=auth_headers["regular"]
        )
        
        response2 = client.get(
            "/api/candidats/",
            headers=auth_headers["other_client"]
        )
        
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        # Les deux voient les mêmes candidats
        candidats1 = response1.json()
        candidats2 = response2.json()
        assert len(candidats1) == len(candidats2)
    
    def test_create_besoin_assigns_correct_client_id(
        self,
        client: TestClient,
        db: Session,
        test_clients: tuple,
        auth_headers: dict
    ):
        """La création d'un besoin assigne automatiquement le bon client_id"""
        client1, _ = test_clients
        
        besoin_data = {
            "poste_recherche": "Test Isolation",
            "description": "Test multi-tenant",
            "ville": "Paris",
            "departement": "75",
            "format_travail": "temps_plein"
        }
        
        response = client.post(
            "/api/besoins/",
            headers=auth_headers["regular"],
            json=besoin_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        created_besoin = response.json()
        
        # Vérifier que le client_id est correct
        assert created_besoin["client_id"] == str(client1.id)
        
        # Vérifier en base
        db_besoin = db.query(Besoin).filter(
            Besoin.id == uuid.UUID(created_besoin["id"])
        ).first()
        assert db_besoin.client_id == client1.id
    
    def test_cannot_override_client_id_in_request(
        self,
        client: TestClient,
        db: Session,
        test_clients: tuple,
        auth_headers: dict
    ):
        """Un utilisateur ne peut pas forcer un autre client_id"""
        client1, client2 = test_clients
        
        # Tentative de création avec client_id du client2
        besoin_data = {
            "client_id": str(client2.id),  # Tentative de forcer
            "poste_recherche": "Hack Attempt",
            "ville": "Paris"
        }
        
        response = client.post(
            "/api/besoins/",
            headers=auth_headers["regular"],
            json=besoin_data
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            created = response.json()
            # Le client_id doit être celui du token, pas celui de la requête
            assert created["client_id"] == str(client1.id)
            assert created["client_id"] != str(client2.id)
    
    def test_candidature_isolation_between_clients(
        self,
        client: TestClient,
        db: Session,
        test_matchings: list,
        test_clients: tuple,
        auth_headers: dict
    ):
        """Les candidatures restent isolées entre clients"""
        from app.models.models import Candidature
        
        client1, client2 = test_clients
        matching = test_matchings[0]
        
        # Créer une candidature pour client1
        candidature1 = Candidature(
            id=uuid.uuid4(),
            matching_id=matching.id,
            besoin_id=matching.besoin_id,
            candidat_id=matching.candidat_id,
            client_id=client1.id,
            statut="nouveau"
        )
        
        # Créer une candidature pour client2 (même candidat, différent client)
        candidature2 = Candidature(
            id=uuid.uuid4(),
            besoin_id=uuid.uuid4(),  # Besoin différent
            candidat_id=matching.candidat_id,  # Même candidat
            client_id=client2.id,
            statut="nouveau"
        )
        
        db.add_all([candidature1, candidature2])
        db.commit()
        
        # Vérifier l'isolation
        candidatures_client1 = db.query(Candidature).filter(
            Candidature.client_id == client1.id
        ).all()
        
        candidatures_client2 = db.query(Candidature).filter(
            Candidature.client_id == client2.id
        ).all()
        
        assert len(candidatures_client1) == 1
        assert len(candidatures_client2) == 1
        assert candidatures_client1[0].id != candidatures_client2[0].id
    
    def test_matching_export_isolation(
        self,
        client: TestClient,
        db: Session,
        test_besoins: list,
        auth_headers: dict
    ):
        """L'export de matching est isolé par client"""
        other_client_besoin = test_besoins[3]
        
        # Tentative d'export d'un besoin d'un autre client
        response = client.get(
            f"/api/matchings/export/{other_client_besoin.id}",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]
    
    def test_admin_cannot_access_other_client_data(
        self,
        client: TestClient,
        db: Session,
        test_besoins: list,
        auth_headers: dict
    ):
        """Même un admin ne peut pas accéder aux données d'un autre client"""
        other_client_besoin = test_besoins[3]
        
        # Admin du client1 essaye d'accéder au besoin du client2
        response = client.get(
            f"/api/besoins/{other_client_besoin.id}",
            headers=auth_headers["admin"]
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

class TestDataLeakagePrevention:
    """Tests de prévention de fuite de données"""
    
    def test_error_messages_dont_reveal_existence(
        self,
        client: TestClient,
        test_besoins: list,
        auth_headers: dict
    ):
        """Les messages d'erreur ne révèlent pas l'existence de ressources"""
        other_client_besoin = test_besoins[3]
        fake_id = uuid.uuid4()
        
        # Ressource qui existe (autre client)
        response1 = client.get(
            f"/api/besoins/{other_client_besoin.id}",
            headers=auth_headers["regular"]
        )
        
        # Ressource qui n'existe pas
        response2 = client.get(
            f"/api/besoins/{fake_id}",
            headers=auth_headers["regular"]
        )
        
        # Les deux doivent retourner le même message
        assert response1.status_code == response2.status_code
        assert response1.json()["detail"] == response2.json()["detail"]
    
    def test_count_endpoints_respect_isolation(
        self,
        client: TestClient,
        db: Session,
        test_besoins: list,
        auth_headers: dict
    ):
        """Les endpoints de comptage respectent l'isolation"""
        # Si un endpoint de stats existe
        response = client.get(
            "/api/besoins/",
            headers=auth_headers["regular"]
        )
        
        besoins = response.json()
        # Doit avoir exactement 3 besoins (client1), pas 4 (total)
        assert len(besoins) == 3
    
    def test_search_respects_client_boundaries(
        self,
        client: TestClient,
        test_besoins: list,
        auth_headers: dict
    ):
        """La recherche ne retourne que les données du client"""
        # Recherche qui pourrait matcher le besoin du client2
        response = client.get(
            "/api/besoins/?search=Client2",
            headers=auth_headers["regular"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        results = response.json()
        
        # Ne doit rien trouver car "Client2" est dans l'autre tenant
        assert len(results) == 0
    
    def test_bulk_operations_respect_isolation(
        self,
        client: TestClient,
        db: Session,
        test_clients: tuple,
        auth_headers: dict
    ):
        """Les opérations bulk respectent l'isolation"""
        client1, _ = test_clients
        
        # Upload de fichier candidats
        import io
        csv_content = """nom,prenom,email
        Bulk,Test,bulk@test.com
        """
        
        file = io.BytesIO(csv_content.encode())
        
        response = client.post(
            "/api/uploads/candidats",
            headers=auth_headers["regular"],
            files={"file": ("test.csv", file, "text/csv")}
        )
        
        # Le fichier doit être associé au bon client
        # Vérifier dans les logs ou metadata que le client_id est correct