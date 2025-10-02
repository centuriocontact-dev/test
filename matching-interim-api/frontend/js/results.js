// frontend/js/results.js

// Gestionnaire des résultats
class ResultsManager {
    constructor() {
        this.results = [];
        this.filteredResults = [];
        this.currentBesoinId = null;
        this.currentPage = 1;
        this.itemsPerPage = config.ITEMS_PER_PAGE || 20;
        this.filters = {
            score: '',
            status: '',
            poste: ''
        };
    }

    init() {
        this.setupFilters();
        this.setupButtons();
        this.setupModal();
        this.loadResults();
    }

    // Setup des filtres
    setupFilters() {
        // Filtre score
        const filterScore = document.getElementById('filter-score');
        if (filterScore) {
            filterScore.addEventListener('change', () => {
                this.filters.score = filterScore.value;
                this.applyFilters();
            });
        }

        // Filtre statut
        const filterStatus = document.getElementById('filter-status');
        if (filterStatus) {
            filterStatus.addEventListener('change', () => {
                this.filters.status = filterStatus.value;
                this.applyFilters();
            });
        }

        // Filtre poste
        const filterPoste = document.getElementById('filter-poste');
        if (filterPoste) {
            filterPoste.addEventListener('change', () => {
                this.filters.poste = filterPoste.value;
                this.applyFilters();
            });
        }

        // Bouton clear filters
        const clearBtn = document.getElementById('btn-clear-filters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearFilters());
        }
    }

    // Setup des boutons
    setupButtons() {
        // Export Excel
        const exportBtn = document.getElementById('btn-export');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportResults());
        }
    }

    // Setup modal
    setupModal() {
        // Boutons contact dans la modal
        const emailBtn = document.getElementById('modal-contact-email');
        if (emailBtn) {
            emailBtn.addEventListener('click', () => this.contactCandidate('email'));
        }

        const phoneBtn = document.getElementById('modal-contact-phone');
        if (phoneBtn) {
            phoneBtn.addEventListener('click', () => this.contactCandidate('phone'));
        }
    }

    // Charger les résultats
    async loadResults(besoinId = null) {
        try {
            // Si un besoin spécifique est demandé
            if (besoinId) {
                this.currentBesoinId = besoinId;
                const matchings = await api.get(
                    config.ENDPOINTS.MATCHING_RESULTS.replace('{id}', besoinId)
                );
                this.processMatchings(matchings);
            } else {
                // Charger tous les résultats récents
                await this.loadAllResults();
            }

            // Mettre à jour l'UI
            this.updateResultsDisplay();
            this.updateFiltersOptions();
            this.updateSummary();

        } catch (error) {
            console.error('Error loading results:', error);
            app.showToast('Erreur de chargement des résultats', 'error');
            this.showEmptyState();
        }
    }

    // Charger tous les résultats
    async loadAllResults() {
        try {
            // Charger tous les besoins avec matchings
            const besoins = await api.get(config.ENDPOINTS.BESOINS, {
                limit: 100
            });

            const allMatchings = [];

            // Pour chaque besoin ayant des matchings
            for (const besoin of besoins) {
                if (besoin.nb_matchings > 0) {
                    try {
                        const matchings = await api.get(
                            config.ENDPOINTS.MATCHING_RESULTS.replace('{id}', besoin.id)
                        );

                        // Ajouter les infos du besoin aux matchings
                        matchings.forEach(m => {
                            m.besoin_info = besoin;
                        });

                        allMatchings.push(...matchings);
                    } catch (e) {
                        console.error(`Error loading matchings for besoin ${besoin.id}:`, e);
                    }
                }
            }

            this.processMatchings(allMatchings);

        } catch (error) {
            console.error('Error loading all results:', error);
            this.results = [];
            this.filteredResults = [];
        }
    }

    // Traiter les matchings
    processMatchings(matchings) {
        this.results = matchings.map(m => ({
            id: m.id,
            candidat_id: m.candidat_id,
            candidat_nom: m.candidat_nom || `Candidat ${m.candidat_id}`,
            besoin_id: m.besoin_id,
            poste: m.besoin_info?.poste_recherche || 'N/A',
            score: Math.round(m.score_total * 100),
            rang: m.rang,
            telephone: m.telephone || 'N/A',
            email: m.email || 'N/A',
            disponibilite: m.disponibilite || 'N/A',
            experience: m.experience || 'N/A',
            points_forts: m.points_forts || [],
            points_faibles: m.points_faibles || [],
            status: this.getStatus(m.score_total * 100)
        }));

        this.filteredResults = [...this.results];
    }

    // Obtenir le statut selon le score
    getStatus(score) {
        if (score >= 90) return 'excellent';
        if (score >= 75) return 'bon';
        if (score >= 50) return 'moyen';
        return 'faible';
    }

    // Appliquer les filtres
    applyFilters() {
        this.filteredResults = this.results.filter(result => {
            // Filtre score
            if (this.filters.score) {
                const minScore = parseInt(this.filters.score);
                if (result.score < minScore) return false;
            }

            // Filtre statut
            if (this.filters.status && result.status !== this.filters.status) {
                return false;
            }

            // Filtre poste
            if (this.filters.poste && result.poste !== this.filters.poste) {
                return false;
            }

            return true;
        });

        this.currentPage = 1;
        this.updateResultsDisplay();
        this.updateSummary();
    }

    // Effacer les filtres
    clearFilters() {
        this.filters = {
            score: '',
            status: '',
            poste: ''
        };

        document.getElementById('filter-score').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-poste').value = '';

        this.filteredResults = [...this.results];
        this.updateResultsDisplay();
        this.updateSummary();
    }

    // Mettre à jour l'affichage des résultats
    updateResultsDisplay() {
        const tbody = document.querySelector('#results-table tbody');
        if (!tbody) return;

        if (this.filteredResults.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center" style="padding: 40px;">
                        <div>📋</div>
                        <div style="font-size: 18px; margin: 10px 0;">Aucun résultat</div>
                        <div style="color: var(--color-text-light);">
                            ${this.results.length > 0 ? 'Essayez de modifier les filtres' : 'Lancez un matching pour voir les résultats'}
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        // Pagination
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        const pageResults = this.filteredResults.slice(start, end);

        // Afficher les résultats
        tbody.innerHTML = '';
        pageResults.forEach(result => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${result.rang || '-'}</td>
                <td><strong>${result.candidat_nom}</strong></td>
                <td>${result.poste}</td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 60px; height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden;">
                            <div style="width: ${result.score}%; height: 100%; background: ${this.getScoreColor(result.score)};"></div>
                        </div>
                        <strong>${result.score}%</strong>
                    </div>
                </td>
                <td>
                    <span class="status-badge status-${result.status}">
                        ${result.status.charAt(0).toUpperCase() + result.status.slice(1)}
                    </span>
                </td>
                <td>
                    <div style="display: flex; gap: 8px;">
                        ${result.email !== 'N/A' ? `<a href="mailto:${result.email}" class="btn btn-small">📧</a>` : ''}
                        ${result.telephone !== 'N/A' ? `<a href="tel:${result.telephone}" class="btn btn-small">📞</a>` : ''}
                    </div>
                </td>
                <td>
                    <button class="btn btn-small" onclick="resultsManager.showCandidateDetails('${result.id}')">
                        Détails
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });

        // Pagination
        this.updatePagination();
    }

    // Mettre à jour la pagination
    updatePagination() {
        const container = document.getElementById('pagination');
        if (!container) return;

        const totalPages = Math.ceil(this.filteredResults.length / this.itemsPerPage);
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = '<div style="display: flex; gap: 8px; justify-content: center; align-items: center; margin-top: 20px;">';
        
        // Previous
        if (this.currentPage > 1) {
            html += `<button class="btn btn-small" onclick="resultsManager.goToPage(${this.currentPage - 1})">←</button>`;
        }

        // Page numbers
        for (let i = 1; i <= Math.min(totalPages, 5); i++) {
            const isActive = i === this.currentPage;
            html += `<button class="btn btn-small ${isActive ? 'btn-primary' : ''}" onclick="resultsManager.goToPage(${i})">${i}</button>`;
        }

        if (totalPages > 5) {
            html += '<span>...</span>';
            html += `<button class="btn btn-small" onclick="resultsManager.goToPage(${totalPages})">${totalPages}</button>`;
        }

        // Next
        if (this.currentPage < totalPages) {
            html += `<button class="btn btn-small" onclick="resultsManager.goToPage(${this.currentPage + 1})">→</button>`;
        }

        html += '</div>';
        container.innerHTML = html;
    }

    // Aller à une page
    goToPage(page) {
        this.currentPage = page;
        this.updateResultsDisplay();
        
        // Scroll to top
        document.querySelector('#results-table').scrollIntoView({ behavior: 'smooth' });
    }

    // Mettre à jour le résumé
    updateSummary() {
        const totalEl = document.getElementById('total-matchings');
        const avgEl = document.getElementById('avg-score');

        if (totalEl) {
            totalEl.textContent = this.filteredResults.length;
        }

        if (avgEl) {
            const avg = this.filteredResults.length > 0
                ? Math.round(this.filteredResults.reduce((sum, r) => sum + r.score, 0) / this.filteredResults.length)
                : 0;
            avgEl.textContent = `${avg}%`;
        }
    }

    // Mettre à jour les options de filtres
    updateFiltersOptions() {
        // Postes uniques
        const postes = [...new Set(this.results.map(r => r.poste))];
        const filterPoste = document.getElementById('filter-poste');
        
        if (filterPoste) {
            const currentValue = filterPoste.value;
            filterPoste.innerHTML = '<option value="">Tous</option>';
            
            postes.forEach(poste => {
                const option = document.createElement('option');
                option.value = poste;
                option.textContent = poste;
                filterPoste.appendChild(option);
            });
            
            filterPoste.value = currentValue;
        }
    }

    // Afficher les détails d'un candidat
    showCandidateDetails(matchingId) {
        const result = this.results.find(r => r.id === matchingId);
        if (!result) return;

        // Remplir la modal
        document.getElementById('modal-candidate-name').textContent = result.candidat_nom;
        document.getElementById('modal-score').textContent = `${result.score}%`;
        document.getElementById('modal-experience').textContent = `${result.experience} ans`;
        document.getElementById('modal-availability').textContent = result.disponibilite;
        document.getElementById('modal-location').textContent = result.poste;

        // Points forts/faibles
        const strengthsList = document.getElementById('modal-strengths');
        const weaknessesList = document.getElementById('modal-weaknesses');

        strengthsList.innerHTML = result.points_forts.length > 0
            ? result.points_forts.map(p => `<li>${p}</li>`).join('')
            : '<li>Aucun point fort identifié</li>';

        weaknessesList.innerHTML = result.points_faibles.length > 0
            ? result.points_faibles.map(p => `<li>${p}</li>`).join('')
            : '<li>Aucun point faible identifié</li>';

        // Stocker les données pour le contact
        this.currentCandidate = result;

        // Ouvrir la modal
        app.openModal('candidate-modal');
    }

    // Contacter un candidat
    contactCandidate(method) {
        if (!this.currentCandidate) return;

        if (method === 'email' && this.currentCandidate.email !== 'N/A') {
            window.location.href = `mailto:${this.currentCandidate.email}?subject=Opportunité: ${this.currentCandidate.poste}`;
        } else if (method === 'phone' && this.currentCandidate.telephone !== 'N/A') {
            window.location.href = `tel:${this.currentCandidate.telephone}`;
        } else {
            app.showToast('Coordonnées non disponibles', 'warning');
        }
    }

    // Exporter les résultats
    async exportResults() {
        if (this.filteredResults.length === 0) {
            app.showToast('Aucun résultat à exporter', 'warning');
            return;
        }

        try {
            // Si on a un besoin spécifique
            if (this.currentBesoinId) {
                await api.download(
                    config.ENDPOINTS.EXPORT_MATCHING.replace('{id}', this.currentBesoinId),
                    `matching_${this.currentBesoinId}_${Date.now()}.xlsx`
                );
            } else {
                // Export personnalisé (créer un CSV simple)
                this.exportToCSV();
            }

            app.showToast('Export réussi !', 'success');

        } catch (error) {
            console.error('Export error:', error);
            app.showToast('Erreur lors de l\'export', 'error');
        }
    }

    // Export CSV simple
    exportToCSV() {
        const headers = ['Rang', 'Candidat', 'Poste', 'Score', 'Statut', 'Email', 'Téléphone'];
        const rows = this.filteredResults.map(r => [
            r.rang || '',
            r.candidat_nom,
            r.poste,
            `${r.score}%`,
            r.status,
            r.email,
            r.telephone
        ]);

        let csv = headers.join(',') + '\n';
        rows.forEach(row => {
            csv += row.map(cell => `"${cell}"`).join(',') + '\n';
        });

        // Créer le fichier
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `matching_results_${Date.now()}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Obtenir la couleur du score
    getScoreColor(score) {
        if (score >= 90) return '#22c55e';
        if (score >= 75) return '#3b82f6';
        if (score >= 50) return '#f59e0b';
        return '#ef4444';
    }

    // Afficher l'état vide
    showEmptyState() {
        const tbody = document.querySelector('#results-table tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center" style="padding: 60px;">
                        <div style="font-size: 48px;">📊</div>
                        <h3>Aucun résultat disponible</h3>
                        <p>Lancez un matching pour voir les résultats ici</p>
                        <button class="btn btn-primary" onclick="app.navigateTo('matching')">
                            Lancer un matching
                        </button>
                    </td>
                </tr>
            `;
        }
    }
}

// Instance globale
const resultsManager = new ResultsManager();

// Fonction pour charger la page de résultats
function loadResultsPage(besoinId = null) {
    resultsManager.loadResults(besoinId);
}

// Initialiser lors du chargement
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('results-page')) {
        resultsManager.init();
    }
});