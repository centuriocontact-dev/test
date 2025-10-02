// frontend/js/upload.js

// Gestionnaire d'upload
class UploadManager {
    constructor() {
        this.files = {
            candidats: null,
            besoins: null
        };
        this.uploadedData = {
            candidats: null,
            besoins: null
        };
    }

    init() {
        this.setupDropzones();
        this.setupButtons();
        this.setupTabs();
    }

    // Setup des dropzones
    setupDropzones() {
        // Dropzone candidats
        this.setupDropzone('candidats');
        
        // Dropzone besoins
        this.setupDropzone('besoins');
    }

    // Setup d'une dropzone
    setupDropzone(type) {
        const dropzone = document.getElementById(`dropzone-${type}`);
        const input = document.getElementById(`file-${type}`);
        
        if (!dropzone || !input) return;

        // Click pour ouvrir le sélecteur
        dropzone.addEventListener('click', () => {
            input.click();
        });

        // Drag and drop events
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0], type);
            }
        });

        // File input change
        input.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0], type);
            }
        });

        // Remove button
        const removeBtn = dropzone.querySelector('.btn-remove');
        if (removeBtn) {
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeFile(type);
            });
        }
    }

    // Gérer la sélection de fichier
    handleFileSelect(file, type) {
        // Validation
        if (!this.validateFile(file)) {
            return;
        }

        // Stocker le fichier
        this.files[type] = file;
        
        // Afficher la preview
        this.showFilePreview(file, type);
        
        // Activer le bouton upload si les deux fichiers sont présents
        this.updateUploadButton();
        
        // Lire et prévisualiser le contenu
        this.previewFileContent(file, type);
    }

    // Valider le fichier
    validateFile(file) {
        // Vérifier l'extension
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!config.ALLOWED_EXTENSIONS.includes(ext)) {
            app.showToast(config.MESSAGES.FILE_INVALID_TYPE, 'error');
            return false;
        }

        // Vérifier la taille (en MB)
        const sizeMB = file.size / (1024 * 1024);
        if (sizeMB > config.MAX_FILE_SIZE) {
            app.showToast(
                config.MESSAGES.FILE_TOO_LARGE.replace('{size}', config.MAX_FILE_SIZE),
                'error'
            );
            return false;
        }

        return true;
    }

    // Afficher la preview du fichier
    showFilePreview(file, type) {
        const dropzone = document.getElementById(`dropzone-${type}`);
        const content = dropzone.querySelector('.dropzone-content');
        const preview = document.getElementById(`preview-${type}`);
        
        // Cacher le contenu, afficher la preview
        content.classList.add('hidden');
        preview.classList.remove('hidden');
        
        // Afficher le nom du fichier
        const fileName = preview.querySelector('.file-name');
        fileName.textContent = file.name;
        
        // Afficher le statut
        const status = document.getElementById(`status-${type}`);
        status.innerHTML = `
            <span class="text-success">✓ Fichier sélectionné (${this.formatFileSize(file.size)})</span>
        `;
    }

    // Retirer un fichier
    removeFile(type) {
        this.files[type] = null;
        this.uploadedData[type] = null;
        
        const dropzone = document.getElementById(`dropzone-${type}`);
        const content = dropzone.querySelector('.dropzone-content');
        const preview = document.getElementById(`preview-${type}`);
        const input = document.getElementById(`file-${type}`);
        const status = document.getElementById(`status-${type}`);
        
        // Réinitialiser l'UI
        content.classList.remove('hidden');
        preview.classList.add('hidden');
        input.value = '';
        status.innerHTML = '';
        
        // Cacher la preview des données
        this.hideDataPreview(type);
        
        // Mettre à jour le bouton
        this.updateUploadButton();
    }

    // Prévisualiser le contenu du fichier
    async previewFileContent(file, type) {
        try {
            const content = await this.readFile(file);
            const data = this.parseFileContent(content, file.name);
            
            if (data && data.length > 0) {
                this.showDataPreview(data, type);
            }
            
        } catch (error) {
            console.error('Error previewing file:', error);
            app.showToast('Impossible de prévisualiser le fichier', 'warning');
        }
    }

    // Lire le fichier
    readFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            
            // Lire selon le type
            if (file.name.endsWith('.csv')) {
                reader.readAsText(file);
            } else {
                reader.readAsArrayBuffer(file);
            }
        });
    }

    // Parser le contenu du fichier
    parseFileContent(content, filename) {
        try {
            if (filename.endsWith('.csv')) {
                return this.parseCSV(content);
            } else {
                // Pour Excel, on devrait utiliser une lib comme SheetJS
                // Pour l'instant, on retourne null
                return null;
            }
        } catch (error) {
            console.error('Parse error:', error);
            return null;
        }
    }

    // Parser CSV simple
    parseCSV(content) {
        const lines = content.split('\n').filter(line => line.trim());
        if (lines.length < 2) return [];
        
        const headers = lines[0].split(/[,;]/).map(h => h.trim());
        const data = [];
        
        for (let i = 1; i < Math.min(6, lines.length); i++) {
            const values = lines[i].split(/[,;]/);
            const row = {};
            headers.forEach((header, index) => {
                row[header] = values[index] ? values[index].trim() : '';
            });
            data.push(row);
        }
        
        return data;
    }

    // Afficher la preview des données
    showDataPreview(data, type) {
        const previewContainer = document.getElementById('data-preview');
        const previewTable = document.getElementById(`preview-table-${type}`);
        
        if (!data || data.length === 0) return;
        
        // Créer le tableau
        let html = '<table class="data-table"><thead><tr>';
        
        // Headers
        const headers = Object.keys(data[0]);
        headers.forEach(header => {
            html += `<th>${header}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        // Rows (max 5)
        data.slice(0, 5).forEach(row => {
            html += '<tr>';
            headers.forEach(header => {
                html += `<td>${row[header] || '-'}</td>`;
            });
            html += '</tr>';
        });
        
        if (data.length > 5) {
            html += `<tr><td colspan="${headers.length}" class="text-center">... et ${data.length - 5} autres lignes</td></tr>`;
        }
        
        html += '</tbody></table>';
        
        previewTable.innerHTML = html;
        previewContainer.classList.remove('hidden');
    }

    // Cacher la preview des données
    hideDataPreview(type) {
        const previewTable = document.getElementById(`preview-table-${type}`);
        if (previewTable) {
            previewTable.innerHTML = '';
        }
        
        // Cacher le container si plus aucune preview
        if (!this.files.candidats && !this.files.besoins) {
            const previewContainer = document.getElementById('data-preview');
            previewContainer.classList.add('hidden');
        }
    }

    // Setup des boutons
    setupButtons() {
        // Bouton upload
        const uploadBtn = document.getElementById('btn-upload');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => this.uploadFiles());
        }
        
        // Bouton reset
        const resetBtn = document.getElementById('btn-reset-upload');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetAll());
        }
    }

    // Setup des tabs
    setupTabs() {
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchTab(tab);
            });
        });
    }

    // Changer d'onglet
    switchTab(tab) {
        // Boutons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        
        // Contenus
        document.querySelectorAll('.preview-table').forEach(content => {
            const isActive = content.id === `preview-table-${tab}`;
            content.classList.toggle('hidden', !isActive);
            content.classList.toggle('active', isActive);
        });
    }

    // Mettre à jour le bouton upload
    updateUploadButton() {
        const btn = document.getElementById('btn-upload');
        if (btn) {
            btn.disabled = !this.files.candidats || !this.files.besoins;
        }
    }

    // Uploader les fichiers
    async uploadFiles() {
        if (!this.files.candidats || !this.files.besoins) {
            app.showToast('Veuillez sélectionner les deux fichiers', 'warning');
            return;
        }

        const uploadBtn = document.getElementById('btn-upload');
        const originalText = uploadBtn.innerHTML;
        
        try {
            // UI loading
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="spinner"></span> Upload en cours...';
            
            // Upload candidats
            app.showToast('Upload du fichier candidats...', 'info');
            const candidatsResponse = await api.upload(
                config.ENDPOINTS.UPLOAD_CANDIDATS,
                this.files.candidats,
                (progress) => this.updateProgress('candidats', progress)
            );
            
            this.uploadedData.candidats = candidatsResponse;
            app.showToast(`${candidatsResponse.candidats_imported || 0} candidats importés`, 'success');
            
            // Upload besoins
            app.showToast('Upload du fichier besoins...', 'info');
            const besoinsResponse = await api.upload(
                config.ENDPOINTS.UPLOAD_BESOINS,
                this.files.besoins,
                (progress) => this.updateProgress('besoins', progress)
            );
            
            this.uploadedData.besoins = besoinsResponse;
            app.showToast(`${besoinsResponse.besoins_imported || 0} besoins importés`, 'success');
            
            // Succès global
            app.showToast('Import terminé avec succès !', 'success');
            
            // Proposer de lancer le matching
            if (confirm('Les fichiers ont été importés avec succès. Voulez-vous lancer le matching maintenant ?')) {
                app.navigateTo('matching');
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            app.showToast(`Erreur d'upload: ${error.message}`, 'error');
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = originalText;
        }
    }

    // Mettre à jour la progression
    updateProgress(type, progress) {
        const status = document.getElementById(`status-${type}`);
        if (status) {
            status.innerHTML = `
                <div class="progress-bar" style="width: 200px; height: 4px; background: #e5e7eb; border-radius: 2px;">
                    <div style="width: ${progress}%; height: 100%; background: #3b82f6; border-radius: 2px; transition: width 0.3s;"></div>
                </div>
                <span style="font-size: 12px; color: #6b7280;">${Math.round(progress)}%</span>
            `;
        }
    }

    // Réinitialiser tout
    resetAll() {
        this.removeFile('candidats');
        this.removeFile('besoins');
        
        const previewContainer = document.getElementById('data-preview');
        previewContainer.classList.add('hidden');
        
        app.showToast('Formulaire réinitialisé', 'info');
    }

    // Formater la taille du fichier
    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
}

// Initialiser lors du chargement de la page
function initUploadPage() {
    const uploadManager = new UploadManager();
    uploadManager.init();
}

// Export pour utilisation globale
window.uploadManager = new UploadManager();