// frontend/js/config.js

// Configuration de l'application
const config = {
    // URL de l'API backend
    API_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000/api'
        : 'https://api.matching-interim.com/api',
    
    // Timeout pour les requêtes API (ms)
    API_TIMEOUT: 30000,
    
    // Durée de vie du token avant refresh (minutes)
    TOKEN_REFRESH_BEFORE: 5,
    
    // Clés localStorage
    STORAGE_KEYS: {
        ACCESS_TOKEN: 'access_token',
        REFRESH_TOKEN: 'refresh_token',
        USER_DATA: 'user_data',
        LAST_PAGE: 'last_page'
    },
    
    // Tailles max fichiers upload (MB)
    MAX_FILE_SIZE: 10,
    
    // Extensions acceptées
    ALLOWED_EXTENSIONS: ['.csv', '.xlsx', '.xls'],
    
    // Pagination
    ITEMS_PER_PAGE: 20,
    
    // Délais animations (ms)
    ANIMATION_DURATION: 300,
    
    // Messages
    MESSAGES: {
        NETWORK_ERROR: 'Erreur de connexion. Vérifiez votre connexion internet.',
        SESSION_EXPIRED: 'Votre session a expiré. Veuillez vous reconnecter.',
        UPLOAD_SUCCESS: 'Fichier uploadé avec succès',
        UPLOAD_ERROR: 'Erreur lors de l\'upload du fichier',
        MATCHING_SUCCESS: 'Matching terminé avec succès',
        MATCHING_ERROR: 'Erreur lors du matching',
        LOGIN_ERROR: 'Email ou mot de passe incorrect',
        LOGOUT_SUCCESS: 'Déconnexion réussie',
        FILE_TOO_LARGE: 'Le fichier est trop volumineux (max {size} MB)',
        FILE_INVALID_TYPE: 'Type de fichier non supporté',
        NO_DATA: 'Aucune donnée à afficher'
    },
    
    // Codes couleur scores
    SCORE_COLORS: {
        EXCELLENT: { min: 90, color: '#22c55e', label: 'Excellent' },
        BON: { min: 75, color: '#3b82f6', label: 'Bon' },
        MOYEN: { min: 50, color: '#f59e0b', label: 'Moyen' },
        FAIBLE: { min: 0, color: '#ef4444', label: 'Faible' }
    },
    
    // Endpoints API
    ENDPOINTS: {
        // Auth
        LOGIN: '/auth/login',
        LOGOUT: '/auth/logout',
        ME: '/auth/me',
        REFRESH: '/auth/refresh',
        
        // Candidats
        CANDIDATS: '/candidats',
        CANDIDAT_DETAIL: '/candidats/{id}',
        
        // Besoins
        BESOINS: '/besoins',
        BESOIN_DETAIL: '/besoins/{id}',
        
        // Matchings
        RUN_MATCHING: '/matchings/run',
        MATCHING_RESULTS: '/matchings/besoin/{id}',
        EXPORT_MATCHING: '/matchings/export/{id}',
        
        // Uploads
        UPLOAD_CANDIDATS: '/uploads/candidats',
        UPLOAD_BESOINS: '/uploads/besoins',
        
        // Health
        HEALTH: '/health',
        HEALTH_DB: '/health/db'
    },
    
    // Configuration des graphiques (si utilisés)
    CHART_OPTIONS: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 500
        }
    }
};

// Rendre la config immutable
Object.freeze(config);
Object.freeze(config.STORAGE_KEYS);
Object.freeze(config.MESSAGES);
Object.freeze(config.ENDPOINTS);
Object.freeze(config.SCORE_COLORS);