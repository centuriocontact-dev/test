// frontend/js/app.js

// Application principale
class MatchingApp {
    constructor() {
        this.currentPage = 'login';
        this.data = {
            candidats: [],
            besoins: [],
            matchings: [],
            stats: {}
        };
    }

    // Initialisation
    async init() {
        // Vérifier l'authentification
        if (auth.init()) {
            // Utilisateur connecté
            this.showMainInterface();
            await this.loadDashboard();
        } else {
            // Non connecté
            this.showLoginPage();
        }

        // Setup event listeners
        this.setupEventListeners();
        
        // Setup navigation
        this.setupNavigation();
        
        // Check responsive
        this.checkResponsive();
        
        window.addEventListener('resize', () => this.checkResponsive());
    }

    // Setup des event listeners
    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // Nav toggle (mobile)
        const navToggle = document.getElementById('nav-toggle');
        if (navToggle) {
            navToggle.addEventListener('click', () => this.toggleNav());
        }

        // Modal close
        document.querySelectorAll('.modal-close, .modal-overlay').forEach(el => {
            el.addEventListener('click', () => this.closeModal());
        });

        // Filter toggle
        const filterToggle = document.getElementById('btn-filter-toggle');
        if (filterToggle) {
            filterToggle.addEventListener('click', () => this.toggleFilters());
        }
    }

    // Setup navigation
    setupNavigation() {
        // Navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.navigateTo(page);
            });
        });

        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.page) {
                this.showPage(e.state.page);
            }
        });
    }

    // Navigation vers une page
    navigateTo(page) {
        // Vérifier l'auth pour les pages protégées
        if (page !== 'login' && !auth.isAuthenticated()) {
            this.showLoginPage();
            return;
        }

        // Fermer la nav mobile
        this.closeNav();

        // Afficher la page
        this.showPage(page);
        
        // Mettre à jour l'URL
        history.pushState({ page }, '', `#${page}`);
        
        // Charger les données de la page
        this.loadPageData(page);
    }

    // Afficher une page
    showPage(page) {
        // Cacher toutes les pages
        document.querySelectorAll('.page').forEach(p => {
            p.classList.add('hidden');
            p.classList.remove('active');
        });

        // Afficher la page demandée
        const pageElement = document.getElementById(`${page}-page`);
        if (pageElement) {
            pageElement.classList.remove('hidden');
            pageElement.classList.add('active');
        }

        // Mettre à jour la nav active
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        this.currentPage = page;
    }

    // Charger les données de la page
    async loadPageData(page) {
        try {
            switch (page) {
                case 'dashboard':
                    await this.loadDashboard();
                    break;
                case 'upload':
                    // Initialisé dans upload.js
                    if (typeof initUploadPage === 'function') {
                        initUploadPage();
                    }
                    break;
                case 'matching':
                    await this.loadMatchingConfig();
                    break;
                case 'results':
                    await this.loadResults();
                    break;
            }
        } catch (error) {
            console.error(`Error loading ${page}:`, error);
            this.showToast(`Erreur de chargement: ${error.message}`, 'error');
        }
    }

    // Login
    async handleLogin(e) {
        e.preventDefault();
        
        const form = e.target;
        const email = form.email.value;
        const password = form.password.value;
        const submitBtn = form.querySelector('button[type="submit"]');
        const errorDiv = document.getElementById('login-error');
        
        // UI loading state
        submitBtn.disabled = true;
        submitBtn.querySelector('.spinner').classList.remove('hidden');
        submitBtn.querySelector('.btn-text').textContent = 'Connexion...';
        errorDiv.textContent = '';

        try {
            await auth.login(email, password);
            
            // Success
            this.showMainInterface();
            this.navigateTo('dashboard');
            this.showToast('Connexion réussie !', 'success');
            
        } catch (error) {
            errorDiv.textContent = error.message || config.MESSAGES.LOGIN_ERROR;
            form.password.value = '';
        } finally {
            submitBtn.disabled = false;
            submitBtn.querySelector('.spinner').classList.add('hidden');
            submitBtn.querySelector('.btn-text').textContent = 'Se connecter';
        }
    }

    // Logout
    async handleLogout() {
        if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
            await auth.logout();
            this.showLoginPage();
            this.showToast(config.MESSAGES.LOGOUT_SUCCESS, 'info');
        }
    }

    // Afficher l'interface principale
    showMainInterface() {
        document.getElementById('login-page').classList.add('hidden');
        document.getElementById('main-nav').classList.remove('hidden');
        document.getElementById('main-content').classList.remove('hidden');
        
        // Afficher les infos utilisateur
        const user = auth.getCurrentUser();
        if (user) {
            document.getElementById('user-email').textContent = user.email;
        }
    }

    // Afficher la page de login
    showLoginPage() {
        document.getElementById('login-page').classList.remove('hidden');
        document.getElementById('login-page').classList.add('active');
        document.getElementById('main-nav').classList.add('hidden');
        document.getElementById('main-content').classList.add('hidden');
    }

    // Charger le dashboard
    async loadDashboard() {
        try {
            // Charger les stats
            const [candidats, besoins] = await Promise.all([
                api.get(config.ENDPOINTS.CANDIDATS, { limit: 100 }),
                api.get(config.ENDPOINTS.BESOINS, { limit: 100 })
            ]);

            // Mettre à jour les métriques
            document.getElementById('metric-candidats').textContent = candidats.length;
            document.getElementById('metric-besoins').textContent = besoins.filter(b => b.statut === 'ouvert').length;
            
            // Message de bienvenue
            const user = auth.getCurrentUser();
            if (user) {
                document.getElementById('welcome-message').textContent = 
                    `Bienvenue ${user.prenom || user.email}`;
            }

            // Charger les derniers matchings
            await this.loadRecentMatchings();
            
        } catch (error) {
            console.error('Dashboard load error:', error);
        }
    }

    // Charger les derniers matchings
    async loadRecentMatchings() {
        try {
            const besoins = await api.get(config.ENDPOINTS.BESOINS, { 
                limit: 5,
                statut: 'ouvert'
            });

            const tbody = document.querySelector('#recent-matchings tbody');
            tbody.innerHTML = '';

            if (besoins.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center">Aucun matching récent</td>
                    </tr>
                `;
                return;
            }

            besoins.forEach(besoin => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${new Date(besoin.created_at).toLocaleDateString('fr-FR')}</td>
                    <td>${besoin.poste_recherche}</td>
                    <td>${besoin.nb_matchings || 0}</td>
                    <td>${besoin.meilleur_score ? `${besoin.meilleur_score}%` : '-'}</td>
                    <td>
                        <button class="btn btn-small" onclick="app.viewBesoinResults('${besoin.id}')">
                            Voir
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
            
        } catch (error) {
            console.error('Recent matchings error:', error);
        }
    }

    // Charger la config matching
    async loadMatchingConfig() {
        try {
            const besoins = await api.get(config.ENDPOINTS.BESOINS, { 
                statut: 'ouvert' 
            });

            const select = document.getElementById('select-besoin');
            select.innerHTML = '<option value="">Tous les besoins ouverts</option>';
            
            besoins.forEach(besoin => {
                const option = document.createElement('option');
                option.value = besoin.id;
                option.textContent = `${besoin.poste_recherche} - ${besoin.ville || 'N/A'}`;
                select.appendChild(option);
            });
            
        } catch (error) {
            console.error('Load matching config error:', error);
        }
    }

    // Charger les résultats
    async loadResults(besoinId = null) {
        // Implémenté dans results.js
        if (typeof loadResultsPage === 'function') {
            loadResultsPage(besoinId);
        }
    }

    // Voir les résultats d'un besoin
    viewBesoinResults(besoinId) {
        this.navigateTo('results');
        this.loadResults(besoinId);
    }

    // Toggle navigation mobile
    toggleNav() {
        const nav = document.getElementById('main-nav');
        nav.classList.toggle('active');
    }

    closeNav() {
        const nav = document.getElementById('main-nav');
        nav.classList.remove('active');
    }

    // Toggle filters
    toggleFilters() {
        const panel = document.getElementById('filters-panel');
        panel.classList.toggle('active');
        
        const btn = document.getElementById('btn-filter-toggle');
        const icon = btn.querySelector('.btn-icon');
        icon.textContent = panel.classList.contains('active') ? '🔼' : '🔽';
    }

    // Modal
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.add('hidden');
        });
        document.body.style.overflow = '';
    }

    // Toast notifications
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        }[type] || 'ℹ️';
        
        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s';
            setTimeout(() => {
                container.removeChild(toast);
            }, 300);
        }, duration);
    }

    // Check responsive
    checkResponsive() {
        const width = window.innerWidth;
        const isMobile = width <= 768;
        const isTablet = width <= 1024;
        
        document.body.classList.toggle('is-mobile', isMobile);
        document.body.classList.toggle('is-tablet', isTablet);
        document.body.classList.toggle('is-desktop', !isTablet);
    }

    // Format date
    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR');
    }

    // Format currency
    formatCurrency(amount) {
        if (!amount) return '-';
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount);
    }

    // Get score color
    getScoreColor(score) {
        if (score >= 90) return config.SCORE_COLORS.EXCELLENT;
        if (score >= 75) return config.SCORE_COLORS.BON;
        if (score >= 50) return config.SCORE_COLORS.MOYEN;
        return config.SCORE_COLORS.FAIBLE;
    }

    // Format score badge
    formatScoreBadge(score) {
        const color = this.getScoreColor(score);
        return `
            <span class="status-badge status-${color.label.toLowerCase()}" 
                  style="background-color: ${color.color}20; color: ${color.color}">
                ${score}% - ${color.label}
            </span>
        `;
    }
}

// Initialiser l'app au chargement
const app = new MatchingApp();

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});