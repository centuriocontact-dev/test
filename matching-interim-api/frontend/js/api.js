// frontend/js/api.js

// Gestionnaire d'API
class APIManager {
    constructor() {
        this.baseURL = config.API_URL;
        this.timeout = config.API_TIMEOUT;
    }

    // Méthode générique pour les requêtes
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        // Configuration par défaut
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            },
            ...options
        };

        // Ajouter le token si disponible
        const token = localStorage.getItem(config.STORAGE_KEYS.ACCESS_TOKEN);
        if (token && !options.skipAuth) {
            defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        }

        // Timeout avec AbortController
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, {
                ...defaultOptions,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // Gérer les erreurs HTTP
            if (!response.ok) {
                await this.handleError(response);
            }

            // Parser la réponse
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return response;

        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('La requête a expiré. Veuillez réessayer.');
            }
            
            throw error;
        }
    }

    // Gestion des erreurs
    async handleError(response) {
        let errorMessage = '';
        
        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.message || '';
        } catch {
            errorMessage = response.statusText;
        }

        switch (response.status) {
            case 401:
                // Token expiré ou invalide
                await auth.handleTokenExpired();
                throw new Error(config.MESSAGES.SESSION_EXPIRED);
            case 403:
                throw new Error('Accès refusé');
            case 404:
                throw new Error('Ressource non trouvée');
            case 422:
                throw new Error(`Données invalides: ${errorMessage}`);
            case 500:
                throw new Error('Erreur serveur. Veuillez réessayer plus tard.');
            default:
                throw new Error(errorMessage || `Erreur ${response.status}`);
        }
    }

    // Méthodes HTTP
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, {
            method: 'GET'
        });
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    // Upload de fichier
    async upload(endpoint, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);

        const token = localStorage.getItem(config.STORAGE_KEYS.ACCESS_TOKEN);
        const headers = {};
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Progress handler
            if (onProgress) {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        onProgress(percentComplete);
                    }
                });
            }

            // Complete handler
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch {
                        resolve(xhr.responseText);
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });

            // Error handler
            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });

            // Abort handler
            xhr.addEventListener('abort', () => {
                reject(new Error('Upload cancelled'));
            });

            // Open and send
            xhr.open('POST', `${this.baseURL}${endpoint}`);
            
            Object.keys(headers).forEach(key => {
                xhr.setRequestHeader(key, headers[key]);
            });
            
            xhr.send(formData);
        });
    }

    // Download file
    async download(endpoint, filename) {
        try {
            const response = await this.request(endpoint, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem(config.STORAGE_KEYS.ACCESS_TOKEN)}`
                }
            });

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            return true;
        } catch (error) {
            console.error('Download error:', error);
            throw error;
        }
    }
}

// Instance globale
const api = new APIManager();