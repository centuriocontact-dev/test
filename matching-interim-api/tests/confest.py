# tests/conftest.py
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from typing import Generator
import os
from passlib.context import CryptContext

# Import app and models
from app.main import app
from app.models.models import Base, User, Client, Candidat, Besoin, Matching
from app.database import get_db
from app.core.security import create_access_token

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://test_user:test_pass@localhost/test_matching_interim"
)

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create test engine
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: Session) -> TestClient:
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def test_clients(db: Session) -> tuple[Client, Client]:
    """Create two test clients for multi-tenant testing"""
    client1 = Client(
        id=uuid.uuid4(),
        code="CLIENT1",
        nom_complet="Client Test 1",
        email_contact="contact1@test.com",
        plan="premium",
        max_besoins=100,
        max_candidats=1000,
        actif=True
    )
    
    client2 = Client(
        id=uuid.uuid4(),
        code="CLIENT2", 
        nom_complet="Client Test 2",
        email_contact="contact2@test.com",
        plan="standard",
        max_besoins=10,
        max_candidats=100,
        actif=True
    )
    
    db.add_all([client1, client2])
    db.commit()
    return client1, client2

@pytest.fixture
def test_users(db: Session, test_clients: tuple[Client, Client]) -> tuple[User, User, User]:
    """Create test users for different clients and roles"""
    client1, client2 = test_clients
    
    # Admin user for client1
    admin_user = User(
        id=uuid.uuid4(),
        client_id=client1.id,
        email="admin@client1.com",
        password_hash=pwd_context.hash("Admin123!"),
        nom="Admin",
        prenom="User",
        role="admin",
        actif=True,
        email_verified=True
    )
    
    # Regular user for client1
    regular_user = User(
        id=uuid.uuid4(),
        client_id=client1.id,
        email="user@client1.com",
        password_hash=pwd_context.hash("User123!"),
        nom="Regular",
        prenom="User",
        role="user",
        actif=True,
        email_verified=True
    )
    
    # User for client2 (isolation test)
    other_client_user = User(
        id=uuid.uuid4(),
        client_id=client2.id,
        email="user@client2.com",
        password_hash=pwd_context.hash("User123!"),
        nom="Other",
        prenom="Client",
        role="user",
        actif=True,
        email_verified=True
    )
    
    db.add_all([admin_user, regular_user, other_client_user])
    db.commit()
    return admin_user, regular_user, other_client_user

@pytest.fixture
def auth_headers(test_users: tuple[User, User, User]) -> dict[str, dict]:
    """Generate auth headers for test users"""
    admin_user, regular_user, other_client_user = test_users
    
    admin_token = create_access_token(
        data={"sub": str(admin_user.id), "client_id": str(admin_user.client_id)}
    )
    
    regular_token = create_access_token(
        data={"sub": str(regular_user.id), "client_id": str(regular_user.client_id)}
    )
    
    other_token = create_access_token(
        data={"sub": str(other_client_user.id), "client_id": str(other_client_user.client_id)}
    )
    
    return {
        "admin": {"Authorization": f"Bearer {admin_token}"},
        "regular": {"Authorization": f"Bearer {regular_token}"},
        "other_client": {"Authorization": f"Bearer {other_token}"}
    }

@pytest.fixture
def test_candidats(db: Session) -> list[Candidat]:
    """Create test candidates"""
    candidats = []
    for i in range(5):
        candidat = Candidat(
            id=uuid.uuid4(),
            nom=f"Candidat{i}",
            prenom=f"Test{i}",
            email=f"candidat{i}@test.com",
            telephone=f"06{i:08d}",
            code_postal=f"{28000+i}",
            ville=f"Ville{i}",
            departement=f"{28+i}",
            metier_principal="Manutentionnaire",
            experience_annees=i+1,
            disponibilite="immediate" if i % 2 == 0 else "1_semaine",
            taux_horaire_min=15.0 + i,
            competences=["manutention", "logistique"],
            actif=True
        )
        candidats.append(candidat)
    
    db.add_all(candidats)
    db.commit()
    return candidats

@pytest.fixture
def test_besoins(db: Session, test_clients: tuple[Client, Client]) -> list[Besoin]:
    """Create test job needs"""
    client1, client2 = test_clients
    
    besoins = []
    
    # Besoins for client1
    for i in range(3):
        besoin = Besoin(
            id=uuid.uuid4(),
            client_id=client1.id,
            poste_recherche=f"Poste {i}",
            description=f"Description du poste {i}",
            ville=f"Ville{i}",
            departement="28",
            format_travail="temps_plein",
            date_debut=datetime.now() + timedelta(days=7),
            experience_requise_min=1.0,
            competences_requises=["manutention"],
            taux_horaire_max=25.0,
            statut="ouvert",
            priorite="normale" if i != 0 else "haute"
        )
        besoins.append(besoin)
    
    # Besoin for client2
    besoin_other = Besoin(
        id=uuid.uuid4(),
        client_id=client2.id,
        poste_recherche="Poste Client2",
        description="Description client 2",
        ville="Paris",
        departement="75",
        format_travail="temps_plein",
        statut="ouvert"
    )
    besoins.append(besoin_other)
    
    db.add_all(besoins)
    db.commit()
    return besoins

@pytest.fixture
def test_matchings(db: Session, test_besoins: list[Besoin], test_candidats: list[Candidat], test_clients: tuple[Client, Client]) -> list[Matching]:
    """Create test matchings"""
    client1, _ = test_clients
    matchings = []
    
    # Create matchings for first besoin
    besoin = test_besoins[0]
    for i, candidat in enumerate(test_candidats[:3]):
        matching = Matching(
            id=uuid.uuid4(),
            besoin_id=besoin.id,
            candidat_id=candidat.id,
            client_id=client1.id,
            score_total=90 - (i * 5),
            score_competences=85 - (i * 5),
            score_localisation=90 - (i * 3),
            score_disponibilite=95 - (i * 2),
            score_financier=88 - (i * 4),
            score_experience=92 - (i * 3),
            rang=i + 1,
            points_forts=["Disponible immédiatement", "Expérience pertinente"],
            points_faibles=["Distance" if i > 0 else None]
        )
        matchings.append(matching)
    
    db.add_all(matchings)
    db.commit()
    return matchings

@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API calls"""
    def mock_completion(*args, **kwargs):
        return {
            "choices": [{
                "message": {
                    "content": "Mocked AI response: excellent match"
                }
            }]
        }
    
    # Mock if OpenAI is used
    monkeypatch.setattr("openai.ChatCompletion.create", mock_completion)
    return mock_completion