# 🧪 Guide des Tests - Matching Intérim Pro

## 📋 Vue d'ensemble

Ce guide explique comment exécuter les tests et le monitoring pour l'application Matching Intérim Pro.

### Structure des tests
```
tests/
├── conftest.py           # Configuration pytest et fixtures
├── test_endpoints.py     # Tests unitaires des endpoints
├── test_multi_tenant.py  # Tests d'isolation multi-tenant (CRITIQUE)
├── test_security.py      # Tests de sécurité
├── test_matching_engine.py # Tests du moteur de matching
├── load_test.py          # Tests de charge
├── pytest.ini           # Configuration pytest
└── requirements-test.txt # Dépendances de test
```

## 🚀 Installation

### 1. Installer les dépendances de test
```bash
# Installation des dépendances principales + test
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 2. Configurer la base de données de test
```bash
# Créer un fichier .env.test
cat > .env.test << EOF
TEST_DATABASE_URL=postgresql://test_user:test_pass@localhost/test_matching_interim
ENVIRONMENT=test
DEBUG=True
USE_OPENAI=False
EOF

# Créer la base de données de test
createdb test_matching_interim
```

## 📊 Exécution des Tests

### Tests Unitaires Rapides (Smoke Tests)
```bash
# Tests essentiels uniquement (~30 secondes)
pytest -m smoke -v

# Avec coverage
pytest -m smoke --cov=app --cov-report=term-missing
```

### Tests Complets
```bash
# Tous les tests avec coverage
pytest --cov=app --cov-report=html

# Ouvrir le rapport de coverage
open htmlcov/index.html
```

### Tests par Catégorie

#### 1. Tests Multi-Tenant (CRITIQUE ⚠️)
```bash
# TRÈS IMPORTANT - Isolation entre clients
pytest tests/test_multi_tenant.py -v

# Avec détails complets
pytest tests/test_multi_tenant.py -vv --tb=long
```

#### 2. Tests de Sécurité
```bash
# Tests auth et injections
pytest tests/test_security.py -v

# Analyse de sécurité avec bandit
bandit -r app/ -ll
```

#### 3. Tests des Endpoints
```bash
# Tests de tous les endpoints API
pytest tests/test_endpoints.py -v

# Un endpoint spécifique
pytest tests/test_endpoints.py::TestCandidatsEndpoints -v
```

#### 4. Tests du Moteur de Matching
```bash
# Tests du matching engine
pytest tests/test_matching_engine.py -v

# Avec performance
pytest tests/test_matching_engine.py::TestMatchingEnginePerformance -v
```

### Tests en Parallèle (Plus Rapide)
```bash
# Utiliser tous les CPU disponibles
pytest -n auto

# Avec 4 workers
pytest -n 4
```

## 🔥 Tests de Charge

### 1. Test de Charge Basique
```bash
# 10 utilisateurs, 5 requêtes chacun
python tests/load_test.py --url http://localhost:8000 --test basic

# Plus de charge
python tests/load_test.py --users 50 --requests 10
```

### 2. Test de Montée en Charge (Stress)
```bash
# Monte progressivement jusqu'à 100 utilisateurs
python tests/load_test.py --test stress
```

### 3. Test de Pic (Spike)
```bash
# Simule un pic soudain de trafic
python tests/load_test.py --test spike
```

### 4. Avec Locust (Alternative)
```bash
# Créer locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class MatchingUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/health")
    
    @task(3)
    def list_candidats(self):
        headers = {"Authorization": "Bearer TOKEN"}
        self.client.get("/api/candidats/", headers=headers)
EOF

# Lancer Locust
locust -f locustfile.py --host=http://localhost:8000
# Ouvrir http://localhost:8089
```

## 🏥 Health Checks et Monitoring

### 1. Health Checks Manuels
```bash
# Health basique
curl http://localhost:8000/health

# Health database
curl http://localhost:8000/health/db

# Health détaillé
curl http://localhost:8000/health/detailed

# Readiness (prêt à recevoir du trafic)
curl http://localhost:8000/health/ready
```

### 2. Monitoring Continu
```bash
# Démarrer le monitoring
python scripts/monitoring.py

# Avec configuration
export MONITOR_API_URL=http://localhost:8000
export MONITOR_INTERVAL=30
export ALERT_WEBHOOK_URL=https://hooks.slack.com/services/xxx
python scripts/monitoring.py
```

### 3. Monitoring avec Watch (Simple)
```bash
# Check toutes les 5 secondes
watch -n 5 'curl -s http://localhost:8000/health | jq'
```

## 📈 Métriques et Rapports

### Générer un Rapport HTML
```bash
# Tests avec rapport HTML
pytest --html=report.html --self-contained-html

# Ouvrir le rapport
open report.html
```

### Coverage Minimum
```bash
# Exige 70% de coverage minimum
pytest --cov=app --cov-fail-under=70
```

### Rapport XML (pour CI/CD)
```bash
# Format JUnit pour Jenkins/GitLab
pytest --junitxml=junit.xml

# Coverage XML pour SonarQube
pytest --cov=app --cov-report=xml
```

## 🔍 Debug et Troubleshooting

### Mode Debug
```bash
# Tests avec breakpoint
pytest --pdb

# S'arrêter au premier échec
pytest -x

# Afficher les prints
pytest -s

# Mode très verbeux
pytest -vvv
```

### Tests Spécifiques
```bash
# Un test unique
pytest tests/test_security.py::TestAuthentication::test_login_success

# Tests contenant "login"
pytest -k login

# Exclure les tests lents
pytest -m "not slow"
```

### Profiling
```bash
# Profile les tests lents
pytest --profile

# Avec durée des tests
pytest --durations=10
```

## 🐳 Tests avec Docker

### Créer l'image de test
```bash
# Dockerfile.test
cat > Dockerfile.test << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements*.txt .
RUN pip install -r requirements.txt -r requirements-test.txt
COPY . .
CMD ["pytest"]
EOF

# Build et run
docker build -f Dockerfile.test -t matching-test .
docker run matching-test
```

### Avec Docker Compose
```bash
# docker-compose.test.yml
cat > docker-compose.test.yml << 'EOF'
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
  
  app:
    build: .
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://test_user:test_pass@db/test_db
    command: pytest
EOF

docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## ✅ Checklist Pré-Production

### Tests Obligatoires
- [ ] **Multi-tenant isolation** : `pytest tests/test_multi_tenant.py`
- [ ] **Sécurité** : `pytest tests/test_security.py`
- [ ] **Endpoints principaux** : `pytest tests/test_endpoints.py`
- [ ] **Coverage > 70%** : `pytest --cov=app --cov-fail-under=70`
- [ ] **Test de charge** : `python tests/load_test.py --test all`

### Vérifications Manuelles
- [ ] Health check accessible : `curl /health`
- [ ] Database responsive : `curl /health/db`
- [ ] Logs structurés JSON en production
- [ ] Variables d'environnement configurées
- [ ] Secrets non exposés dans les logs

### Monitoring
- [ ] Script monitoring configuré
- [ ] Alertes email/webhook testées
- [ ] Health checks automatiques configurés sur Render.com
- [ ] Logs centralisés accessibles

## 🚨 Tests Critiques Multi-Tenant

**⚠️ ATTENTION : Ces tests sont CRITIQUES pour la sécurité**

```bash
# Toujours exécuter avant déploiement
pytest tests/test_multi_tenant.py -v

# Points vérifiés :
# - Un client ne peut JAMAIS voir les données d'un autre
# - Les besoins sont isolés par client_id
# - Les matchings respectent les frontières
# - Pas de fuite dans les messages d'erreur
```

## 📝 Scripts Utiles

### Test complet avant déploiement
```bash
#!/bin/bash
# pre-deploy-test.sh

echo "🧪 Tests pré-déploiement..."

# 1. Tests unitaires
pytest -m "not slow" --cov=app --cov-fail-under=70 || exit 1

# 2. Tests multi-tenant (CRITIQUE)
pytest tests/test_multi_tenant.py -v || exit 1

# 3. Tests de sécurité
pytest tests/test_security.py -v || exit 1

# 4. Test de charge basique
python tests/load_test.py --test basic --users 20 || exit 1

# 5. Health checks
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:8000/health/db || exit 1

echo "✅ Tous les tests passent !"
```

### Monitoring local
```bash
#!/bin/bash
# monitor-local.sh

while true; do
    clear
    echo "📊 Monitoring - $(date)"
    echo "========================"
    
    # Health
    echo -n "Health: "
    curl -s http://localhost:8000/health | jq -r .status
    
    # Database
    echo -n "Database: "
    curl -s http://localhost:8000/health/db | jq -r .status
    
    # Stats
    curl -s http://localhost:8000/health/db | jq .stats
    
    sleep 5
done
```

## 🆘 Support et Aide

### En cas de problème

1. **Tests qui échouent**
   - Vérifier la base de données : `psql test_matching_interim`
   - Nettoyer le cache : `pytest --cache-clear`
   - Réinstaller les dépendances : `pip install -r requirements-test.txt --force-reinstall`

2. **Problèmes de performance**
   - Profiler : `pytest --profile-svg`
   - Identifier les tests lents : `pytest --durations=0`

3. **Erreurs multi-tenant**
   - **CRITIQUE** : Ne jamais ignorer ces erreurs
   - Vérifier les fixtures de client_id
   - Tracer les requêtes SQL

## 📚 Ressources

- [Documentation Pytest](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)