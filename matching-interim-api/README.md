# 🎯 Matching Intérim Pro - API FastAPI

API REST complète pour le matching intelligent candidats-besoins.

## 📋 Prérequis

- Python 3.11+
- PostgreSQL 14+
- pip

## 🚀 Installation rapide

### 1. Cloner le projet
```bash
git clone <votre-repo>
cd matching-interim-api
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec vos paramètres
nano .env  # ou votre éditeur préféré
```

### 5. Initialiser la base de données
```bash
# Créer la base
createdb matching_interim

# Exécuter le script SQL
psql -U matching_user -d matching_interim -f init_db.sql

# Ou utiliser SQLAlchemy
python
>>> from app.database import engine
>>> from app.models.models import Base
>>> Base.metadata.create_all(engine)
>>> exit()
```

### 6. Créer un utilisateur de test
```python
from app.database import SessionLocal
from app.models.models import Client, User
from app.core.security import get_password_hash
import uuid

db = SessionLocal()

# Créer un client
client = Client(
    code="demo",
    nom_complet="Entreprise Demo",
    email_contact="demo@example.com"
)
db.add(client)
db.flush()

# Créer un utilisateur
user = User(
    client_id=client.id,
    email="admin@demo.fr",
    password_hash=get_password_hash("demo123"),
    nom="Admin",
    prenom="Demo",
    role="admin",
    actif=True
)
db.add(user)
db.commit()
```

### 7. Lancer le serveur
```bash
uvicorn app.main:app --reload
```

L'API est maintenant accessible sur : http://localhost:8000

## 📖 Documentation

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## 🔑 Endpoints principaux

### Authentification
```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@demo.fr&password=demo123"

# Retourne:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {...}
}
```

### Upload Candidats
```bash
curl -X POST "http://localhost:8000/api/uploads/candidats" \
  -H "Authorization: Bearer <votre_token>" \
  -F "file=@candidats.csv"
```

### Upload Besoins
```bash
curl -X POST "http://localhost:8000/api/uploads/besoins" \
  -H "Authorization: Bearer <votre_token>" \
  -F "file=@besoins.xlsx"
```

### Lancer un Matching
```bash
curl -X POST "http://localhost:8000/api/matchings/run" \
  -H "Authorization: Bearer <votre_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "besoin_id": null,
    "use_ai": false,
    "force_refresh": false
  }'
```

### Récupérer les résultats
```bash
# Liste des matchings pour un besoin
curl -X GET "http://localhost:8000/api/matchings/besoin/{besoin_id}" \
  -H "Authorization: Bearer <votre_token>"

# Export Excel
curl -X GET "http://localhost:8000/api/matchings/export/{besoin_id}" \
  -H "Authorization: Bearer <votre_token>" \
  --output matching_results.xlsx
```

## 📁 Structure du projet

```
matching-interim-api/
├── app/
│   ├── main.py              # Point d'entrée
│   ├── config.py            # Configuration
│   ├── database.py          # Connexion DB
│   ├── models/
│   │   └── models.py        # Modèles SQLAlchemy
│   ├── schemas/             # Schémas Pydantic
│   ├── routers/             # Routes API
│   ├── core/                # Sécurité & middleware
│   ├── services/            # Logique métier
│   └── utils/               # Utilitaires
├── matching_engine.py       # Votre moteur (non modifié)
├── uploads/                 # Fichiers uploadés
├── data/                    # Data clients
├── requirements.txt
├── .env
└── README.md
```

## 🔧 Configuration avancée

### Utiliser PostgreSQL distant
```bash
# Dans .env
DATABASE_URL=postgresql://user:pass@remote-host:5432/dbname
```

### Activer l'IA GPT
```bash
# Dans .env
OPENAI_API_KEY=sk-...

# Puis dans l'appel API
{
  "use_ai": true
}
```

### CORS personnalisé
```bash
# Dans .env
CORS_ORIGINS=http://localhost:3000,https://monsite.com
```

## 🧪 Tests

```bash
# Installer pytest
pip install pytest pytest-asyncio httpx

# Lancer les tests
pytest tests/ -v
```

## 📦 Déploiement

### Docker
```bash
# Construire l'image
docker build -t matching-api .

# Lancer le conteneur
docker run -p 8000:8000 --env-file .env matching-api
```

### Heroku
```bash
heroku create matching-interim-api
git push heroku main
```

## 🐛 Dépannage

### Erreur de connexion DB
```bash
# Vérifier PostgreSQL
psql -U matching_user -d matching_interim

# Vérifier les credentials dans .env
```

### Import error matching_engine
```bash
# S'assurer que matching_engine.py est à la racine
ls matching_engine.py

# Vérifier les imports Python
python -c "from matching_engine import OptimizedInterimMatcher"
```

### Problème JWT
```bash
# Vérifier que SECRET_KEY fait au moins 32 caractères
# Générer une nouvelle clé
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📞 Support

Pour toute question : support@matching-pro.fr

## 📄 Licence

MIT License - voir LICENSE file