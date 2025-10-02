// frontend/js/auth.js

// Gestionnaire d'authentification
class AuthManager {
    constructor() {
        this.user = null;
        this.tokenRefreshTimer = null;
    }

    // Initialiser l'auth au chargement
    init() {
        const token = localStorage.getItem(config.STORAGE_KEYS.ACCESS_TOKEN);
        const userData = localStorage.getItem(config.STORAGE_KEYS.USER_DATA);
        
        if (token && userData) {
            try {
                this.user = JSON.parse(userData);
                this.startTokenRefreshTimer();
                return true;
            } catch (e) {
                console.error('Invalid stored user data');
                this.logout();
                return false;
            }
        }
        
        return false;
    }

    // Login
    async login(email, password) {
        try {
            // Créer FormData pour OAuth2
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(`${config.API_URL}${config.ENDPOINTS.LOGIN}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || config.MESSAGES.LOGIN_ERROR);
            }

            const data = await response.json();
            
            // Stocker les tokens et données utilisateur
            localStorage.setItem(config.STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
            localStorage.setItem(config.STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
            localStorage.setItem(config.STORAGE_KEYS.USER_DATA, JSON.stringify(data.user));
            
            this.user = data.user;
            
            // Démarrer le timer de refresh
            this.startTokenRefreshTimer();
            
            return data;
            
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    // Logout
    async logout() {
        try {
            const token = localStorage.getItem(config.STORAGE_KEYS.ACCESS_TOKEN);
            
            if (token) {
                // Appeler l'API de logout
                await api.post(config.ENDPOINTS.LOGOUT);
            }
        } catch (error) {
            console.error('Logout API error:', error);
        } finally {
            // Nettoyer le storage local
            this.clearAuth();
            
            // Rediriger vers login
            window.location.href = '/';
        }
    }

    // Nettoyer l'authentification
    clearAuth() {
        localStorage.removeItem(config.STORAGE_KEYS.ACCESS_TOKEN);
        localStorage.removeItem(config.STORAGE_KEYS.REFRESH_TOKEN);
        localStorage.removeItem(config.STORAGE_KEYS.USER_DATA);
        
        this.user = null;
        
        if (this.tokenRefreshTimer) {
            clearTimeout(this.tokenRefreshTimer);
            this.tokenRefreshTimer = null;
        }
    }

    // Vérifier si l'utilisateur est connecté
    isAuthenticated() {
        return !!localStorage.getItem(config.STORAGE_KEYS.ACCESS_TOKEN);
    }

    // Obtenir l'utilisateur courant
    getCurrentUser() {
        if (!this.user) {
            const userData = localStorage.getItem(config.STORAGE_KEYS.USER_DATA);
            if (userData) {
                try {
                    this.user = JSON.parse(userData);
                } catch (e) {
                    console.error('Invalid user data in storage');
                    return null;
                }
            }
        }
        return this.user;
    }

    // Refresh token
    async refreshToken() {
        try {
            const refreshToken = localStorage.getItem(config.STORAGE_KEYS.REFRESH_TOKEN);
            
            if (!refreshToken) {
                throw new Error('No refresh token');
            }

            const response = await fetch(`${config.API_URL}${config.ENDPOINTS.REFRESH}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            
            // Mettre à jour les tokens
            localStorage.setItem(config.STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
            if (data.refresh_token) {
                localStorage.setItem(config.STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
            }
            
            // Redémarrer le timer
            this.startTokenRefreshTimer();
            
            return true;
            
        } catch (error) {
            console.error('Token refresh error:', error);
            this.clearAuth();
            return false;
        }
    }

    // Timer pour refresh automatique
    startTokenRefreshTimer() {
        if (this.tokenRefreshTimer) {
            clearTimeout(this.tokenRefreshTimer);
        }
        
        // Refresh 5 minutes avant expiration (25 minutes pour un token de 30 min)
        const refreshTime = (30 - config.TOKEN_REFRESH_BEFORE) * 60 * 1000;
        
        this.tokenRefreshTimer = setTimeout(() => {
            this.refreshToken();
        }, refreshTime);
    }

    // Gérer l'expiration du token
    async handleTokenExpired() {
        const refreshed = await this.refreshToken();
        
        if (!refreshed) {
            this.clearAuth();
            app.showToast('Session expirée. Veuillez vous reconnecter.', 'warning');
            app.navigateTo('login');
        }
        
        return refreshed;
    }

    // Vérifier et obtenir les infos utilisateur
    async checkAuth() {
        try {
            const response = await api.get(config.ENDPOINTS.ME);
            
            this.user = response;
            localStorage.setItem(config.STORAGE_KEYS.USER_DATA, JSON.stringify(response));
            
            return response;
            
        } catch (error) {
            console.error('Auth check failed:', error);
            this.clearAuth();
            throw error;
        }
    }

    // Obtenir les headers d'authentification
    getAuthHeaders() {
        const token = localStorage.getItem(config.STORAGE_KEYS.ACCESS_TOKEN);
        
        if (token) {
            return {
                'Authorization': `Bearer ${token}`
            };
        }
        
        return {};
    }

    // Décoder JWT (pour debug)
    decodeToken(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));

            return JSON.parse(jsonPayload);
        } catch (e) {
            console.error('Error decoding token:', e);
            return null;
        }
    }

    // Vérifier si le token est expiré
    isTokenExpired() {
        const token = localStorage.getItem(config.STORAGE_KEYS.ACCESS_TOKEN);
        
        if (!token) {
            return true;
        }
        
        const decoded = this.decodeToken(token);
        
        if (!decoded || !decoded.exp) {
            return true;
        }
        
        // Vérifier l'expiration (exp est en secondes)
        const now = Date.now() / 1000;
        return decoded.exp < now;
    }
}

// Instance globale
const auth = new AuthManager();