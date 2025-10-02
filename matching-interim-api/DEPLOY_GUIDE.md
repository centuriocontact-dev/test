# 🚀 Guide de Déploiement sur Render.com

Guide complet pour déployer Matching Intérim Pro sur Render.com en moins de 30 minutes.

## 📋 Prérequis

- Compte GitHub avec le code poussé
- Compte Render.com (gratuit)
- (Optionnel) Nom de domaine personnalisé

## 💰 Budget Estimé

### Option 1 : Render Standard (Recommandé)
- **PostgreSQL** : 7$/mois (Starter - 256MB RAM, 1GB stockage)
- **API Backend** : 0$/mois (Free tier - 512MB RAM)
- **Frontend** : 0$/mois (Static site gratuit)
- **Total** : ~7$/mois

### Option 2 : 100% Gratuit (Limitations)
- **PostgreSQL** : Neon.tech (gratuit - suspend après 5min inactivité)
- **API Backend** : Render Free (spin down après 15min)
- **Frontend** : Render Static (gratuit)
- **Total** : 0$/mois

## 📝 Étapes de Déploiement

### Étape 1 : Préparer le Code

1. **Pusher le code sur GitHub**
```bash
git add .
git commit -m "Ready for deployment"
git push origin main