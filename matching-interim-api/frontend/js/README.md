# Interface Web Matching Intérim Pro 📱💼

Interface web responsive optimisée pour tablettes et mobiles pour l'application de matching candidats-missions.

## 🎯 Caractéristiques

- ✅ **100% Responsive** : Optimisé pour tablettes (iPad, Samsung Tab) et mobiles
- ✅ **Touch-friendly** : Zones tactiles minimum 44x44px
- ✅ **Sans framework** : JavaScript vanilla pour performance maximale
- ✅ **JWT Auth** : Gestion sécurisée des tokens
- ✅ **Offline-capable** : LocalStorage pour données temporaires

## 📁 Structure des fichiers

```
frontend/
├── index.html          # Page principale
├── css/
│   ├── styles.css      # Styles principaux
│   └── responsive.css  # Media queries et responsive
├── js/
│   ├── config.js       # Configuration globale
│   ├── api.js          # Gestionnaire API
│   ├── auth.js         # Authentification
│   ├── app.js          # Application principale
│   ├── upload.js       # Upload de fichiers
│   ├── matching.js     # Configuration matching
│   └── results.js      # Affichage résultats
└── README.md           # Ce fichier
```

## 🚀 Installation

### 1. Configuration API

Modifier `js/config.js` pour pointer vers votre API :

```javascript
API_URL: 'http://localhost:8000/api'  // Dev
// ou
API_URL: 'https://api.matching-interim.com/api'  // Production
```

### 2. Serveur local (développement)

#### Option 1 : Python
```bash
cd frontend
python -m http.server 3000
# Ouvrir http://localhost:3000
```

#### Option 2 : Node.js
```bash
npx http-server frontend -p 3000
# Ouvrir http://localhost:3000
```

#### Option 3 : VS Code Live Server
- Installer l'extension "Live Server"
- Clic droit sur `index.html` → "Open with Live Server"

### 3. Déploiement production

Voir la section [Déploiement](#-déploiement) ci-dessous.

## 📱 Utilisation

### Connexion
1. Email : `user@client1.com`
2. Mot de passe : `User123!`

### Workflow type
1. **Upload** : Importer fichiers candidats et besoins
2. **Matching** : Configurer et lancer l'analyse
3. **Résultats** : Consulter et exporter les matchings

### Raccourcis tactiles
- **Swipe gauche/droite** : Navigation entre pages (sur mobile)
- **Tap long** : Options supplémentaires
- **Pinch zoom** : Zoom sur tableaux (désactivé par défaut)

## 🔧 Configuration avancée

### Variables CSS personnalisables

Dans `css/styles.css`, modifier les variables :

```css
:root {
    --color-primary: #2563eb;      /* Couleur principale */
    --font-size-base: 16px;        /* Taille police de base */
    --touch-target: 44px;          /* Zone tactile minimum */
    --button-height: 48px;         /* Hauteur boutons */
}
```

### Paramètres API

Dans `js/config.js` :

```javascript
MAX_FILE_SIZE: 10,              // Taille max upload (MB)
API_TIMEOUT: 30000,             // Timeout requêtes (ms)
ITEMS_PER_PAGE: 20,            // Pagination
TOKEN_REFRESH_BEFORE: 5        // Refresh token (minutes)
```

## 🖥️ Compatibilité

### Navigateurs supportés
- ✅ Chrome 90+
- ✅ Safari 14+ (iOS)
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Samsung Internet 14+

### Appareils testés
- **Tablettes** : iPad (tous), iPad Pro, Samsung Tab S7/S8, Surface
- **Mobiles** : iPhone 12+, Samsung S20+, Pixel 5+
- **Desktop** : Chrome, Firefox, Safari

## 🚢 Déploiement

### Nginx Configuration

Créer `/etc/nginx/sites-available/matching-interim` :

```nginx
server {
    listen 80;
    server_name app.matching-interim.com;
    root /var/www/matching-interim/frontend;
    index index.html;

    # Compression
    gzip on;
    gzip_types text/css application/javascript;

    # Cache static assets
    location ~* \.(css|js)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
}
```

### Apache Configuration

Créer `.htaccess` :

```apache
RewriteEngine On
RewriteBase /

# Force HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]

# SPA routing
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]

# Compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/css application/javascript
</IfModule>

# Cache
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css "access plus 1 week"
    ExpiresByType application/javascript "access plus 1 week"
</IfModule>
```

### Docker

Créer `Dockerfile` :

```dockerfile
FROM nginx:alpine
COPY frontend /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build et run :
```bash
docker build -t matching-interim-web .
docker run -p 80:80 matching-interim-web
```

## 🐛 Troubleshooting

### Problème : "Session expirée" fréquent
- Vérifier la config `TOKEN_REFRESH_BEFORE`
- Vérifier l'horloge système synchronisée

### Problème : Upload échoue
- Vérifier `MAX_FILE_SIZE` dans config
- Vérifier les permissions CORS sur l'API

### Problème : Interface lente sur mobile
- Réduire `ITEMS_PER_PAGE`
- Activer la compression sur le serveur
- Vérifier la taille des images

### Problème : Boutons trop petits sur tablette
- Augmenter `--touch-target` dans CSS
- Augmenter `--button-height`

## 📊 Performance

### Métriques cibles
- **First Paint** : < 1s
- **Interactive** : < 2s
- **Lighthouse Score** : > 90

### Optimisations
1. Minifier CSS/JS en production
2. Activer compression gzip
3. Utiliser CDN pour assets
4. Lazy loading des résultats

## 🔒 Sécurité

- ✅ Tokens JWT stockés en localStorage
- ✅ Auto-logout après inactivité
- ✅ Validation côté client ET serveur
- ✅ HTTPS obligatoire en production
- ✅ Headers sécurité (CSP, X-Frame-Options)

## 📞 Support

Pour toute question ou problème :
1. Vérifier cette documentation
2. Consulter les logs console (F12)
3. Contacter l'équipe technique

## 📝 Licence

Propriétaire - Matching Intérim Pro © 2024