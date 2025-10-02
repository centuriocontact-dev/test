// frontend/js/matching.js

// Gestionnaire de matching
class MatchingManager {
    constructor() {
        this.config = {
            besoin_id: null,
            score_min: 40,
            nb_candidats: 5,
            use_ai: false
        };
        this.isRunning = false;
        this.results = null;
    }

    init() {
        this.setupSliders();
        this.setupButtons();
        this.setupCheckboxes();
        this.loadBesoins();
    }

    // Setup des sliders
    setupSliders() {
        // Score minimum
        const scoreSlider = document.getElementById('score-min');
        const scoreValue = document.getElementById('score-min-value');
        
        if (scoreSlider && scoreValue) {
            scoreSlider.addEventListener('input', (e) => {
                const value = e.target.value;
                this.config.score_min = parseInt(value);
                scoreValue.textContent = `${value}%`;
            });
        }

        // Nombre de candidats
        const nbSlider = document.getElementById('nb-candidats');
        const nbValue = document.getElementById('nb-candidats-value');
        
        if (nbSlider && nbValue) {
            nbSlider.addEventListener('input', (e) => {
                const value = e.target.value;
                this.config.nb_candidats = parseInt(value);
                nbValue.textContent = value;
            });
        }
    }

    // Setup des boutons
    setupButtons() {
        // Bouton lancer matching
        const runBtn = document.getElementById('btn-run-matching');
        if (runBtn) {
            runBtn.addEventListener('click', () => this.runMatching());
        }

        // Bouton preview
        const previewBtn = document.getElementById('btn-preview-matching');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.previewMatching());
        }

        // Sélection besoin
        const selectBesoin = document.getElementById('select-besoin');
        if (selectBesoin) {
            selectBesoin.addEventListener('change', (e) => {
                this.config.besoin_id = e.target.value || null;
            });
        }
    }

    // Setup des checkboxes
    setupCheckboxes() {
        const useAI = document.getElementById('use-ai');
        if (useAI) {
            useAI.addEventListener('change', (e) => {
                this.config.use_ai = e.target.checked;
            });
        }
    }

    // Charger les besoins
    async loadBesoins() {
        try {
            const besoins = await api.get(config.ENDPOINTS.BESOINS, {
                statut: 'ouvert',
                limit: 100
            });

            const select = document.getElementById('select-besoin');
            if (!select) return;

            select.innerHTML = '<option value="">Tous les besoins ouverts</option>';
            
            besoins.forEach(besoin => {
                const option = document.createElement('option');
                option.value = besoin.id;
                option.textContent = `${besoin.poste_recherche} - ${besoin.ville || 'N/A'}`;
                if (besoin.priorite === 'haute') {
                    option.textContent += ' ⭐';
                }
                select.appendChild(option);
            });

            // Si un seul besoin, le sélectionner
            if (besoins.length === 1) {
                select.value = besoins[0].id;
                this.config.besoin_id = besoins[0].id;
            }

        } catch (error) {
            console.error('Error loading besoins:', error);
            app.showToast('Erreur de chargement des besoins', 'error');
        }
    }

    // Preview matching
    async previewMatching() {
        if (this.isRunning) {
            app.showToast('Un matching est déjà en cours', 'warning');
            return;
        }

        try {
            // Validation
            const candidats = await api.get(config.ENDPOINTS.CANDIDATS, { limit: 1 });
            const besoins = await api.get(config.ENDPOINTS.BESOINS, { statut: 'ouvert', limit: 1 });

            if (candidats.length === 0) {
                app.showToast('Aucun candidat disponible. Veuillez d\'abord importer des candidats.', 'warning');
                app.navigateTo('upload');
                return;
            }

            if (besoins.length === 0) {
                app.showToast('Aucun besoin ouvert. Veuillez d\'abord importer des besoins.', 'warning');
                app.navigateTo('upload');
                return;
            }

            // Afficher les infos
            let message = `Configuration du matching:\n\n`;
            message += `• ${this.config.besoin_id ? '1 besoin spécifique' : `${besoins.length} besoins ouverts`}\n`;
            message += `• Score minimum: ${this.config.score_min}%\n`;
            message += `• Candidats par poste: ${this.config.nb_candidats}\n`;
            message += `• Utilisation IA: ${this.config.use_ai ? 'Oui' : 'Non'}\n\n`;
            message += `${candidats.length} candidats disponibles seront analysés.`;

            alert(message);

        } catch (error) {
            console.error('Preview error:', error);
            app.showToast('Erreur lors de la prévisualisation', 'error');
        }
    }

    // Lancer le matching
    async runMatching() {
        if (this.isRunning) {
            app.showToast('Un matching est déjà en cours', 'warning');
            return;
        }

        // Validation
        if (!confirm('Lancer le matching avec les paramètres actuels ?')) {
            return;
        }

        const runBtn = document.getElementById('btn-run-matching');
        const originalContent = runBtn.innerHTML;
        const progressContainer = document.getElementById('matching-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        try {
            this.isRunning = true;

            // UI loading
            runBtn.disabled = true;
            runBtn.innerHTML = '<span class="spinner"></span> Matching en cours...';
            progressContainer.classList.remove('hidden');
            
            // Simulation de progression
            this.simulateProgress(progressFill, progressText);

            // Préparer les données
            const requestData = {
                besoin_id: this.config.besoin_id || null,
                use_ai: this.config.use_ai,
                force_refresh: true,
                config: {
                    score_min: this.config.score_min,
                    nb_candidats: this.config.nb_candidats
                }
            };

            // Lancer le matching
            const response = await api.post(config.ENDPOINTS.RUN_MATCHING, requestData);
            
            // Arrêter la simulation
            clearInterval(this.progressTimer);
            progressFill.style.width = '100%';
            progressText.textContent = 'Matching terminé !';

            // Stocker les résultats
            this.results = response;

            // Afficher le résumé
            const message = `Matching terminé avec succès !\n\n` +
                           `• ${response.besoins_processed || 0} besoins traités\n` +
                           `• ${response.matchings_created || 0} matchings créés\n` +
                           `• Durée: ${response.duration_ms ? (response.duration_ms/1000).toFixed(1) + 's' : 'N/A'}`;
            
            app.showToast(message, 'success');

            // Proposer de voir les résultats
            setTimeout(() => {
                if (confirm('Matching terminé ! Voulez-vous voir les résultats ?')) {
                    app.navigateTo('results');
                }
            }, 1000);

        } catch (error) {
            console.error('Matching error:', error);
            app.showToast(`Erreur lors du matching: ${error.message}`, 'error');
            
            // Reset progress
            clearInterval(this.progressTimer);
            progressFill.style.width = '0%';
            progressText.textContent = 'Erreur';
            
        } finally {
            this.isRunning = false;
            runBtn.disabled = false;
            runBtn.innerHTML = originalContent;
            
            // Cacher la progress après 2s
            setTimeout(() => {
                progressContainer.classList.add('hidden');
                progressFill.style.width = '0%';
            }, 2000);
        }
    }

    // Simuler la progression
    simulateProgress(progressFill, progressText) {
        let progress = 0;
        const steps = [
            { percent: 10, text: 'Initialisation...' },
            { percent: 25, text: 'Chargement des candidats...' },
            { percent: 40, text: 'Chargement des besoins...' },
            { percent: 60, text: 'Analyse des compétences...' },
            { percent: 75, text: 'Calcul des scores...' },
            { percent: 90, text: 'Génération des résultats...' },
            { percent: 95, text: 'Finalisation...' }
        ];

        let currentStep = 0;

        this.progressTimer = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                progressFill.style.width = `${step.percent}%`;
                progressText.textContent = step.text;
                currentStep++;
            }
        }, 1500);
    }

    // Obtenir la configuration actuelle
    getConfig() {
        return { ...this.config };
    }

    // Obtenir les derniers résultats
    getLastResults() {
        return this.results;
    }

    // Réinitialiser
    reset() {
        this.config = {
            besoin_id: null,
            score_min: 40,
            nb_candidats: 5,
            use_ai: false
        };

        // Reset UI
        const scoreSlider = document.getElementById('score-min');
        if (scoreSlider) scoreSlider.value = 40;
        
        const nbSlider = document.getElementById('nb-candidats');
        if (nbSlider) nbSlider.value = 5;
        
        const useAI = document.getElementById('use-ai');
        if (useAI) useAI.checked = false;
        
        const selectBesoin = document.getElementById('select-besoin');
        if (selectBesoin) selectBesoin.value = '';
    }
}

// Instance globale
const matchingManager = new MatchingManager();

// Initialiser lors du chargement de la page matching
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('matching-page')) {
        matchingManager.init();
    }
});