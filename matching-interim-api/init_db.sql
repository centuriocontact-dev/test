-- init_db.sql
-- Script d'initialisation de la base de données Matching Intérim Pro
-- PostgreSQL 14+

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Clients
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL CHECK (code ~ '^[a-z0-9_]+$'),
    nom_complet VARCHAR(200) NOT NULL,
    logo VARCHAR(10),
    couleur VARCHAR(7),
    email_contact VARCHAR(255),
    telephone VARCHAR(20),
    config JSONB DEFAULT '{}',
    plan VARCHAR(50) DEFAULT 'standard',
    max_besoins INTEGER DEFAULT 10,
    max_candidats INTEGER DEFAULT 100,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clients_actif ON clients(actif) WHERE actif = TRUE;

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    telephone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'user', 'readonly')),
    permissions JSONB DEFAULT '[]',
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_client ON users(client_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_actif ON users(actif) WHERE actif = TRUE;

-- Candidats
CREATE TABLE candidats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_externe VARCHAR(50),
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    telephone VARCHAR(20),
    date_naissance DATE,
    code_postal VARCHAR(10),
    ville VARCHAR(100),
    departement VARCHAR(5),
    mobilite_km INTEGER DEFAULT 30,
    permis_conduire BOOLEAN DEFAULT FALSE,
    vehicule BOOLEAN DEFAULT FALSE,
    experience_annees NUMERIC(4,1),
    metier_principal VARCHAR(100),
    competences JSONB DEFAULT '[]',
    niveau_etude VARCHAR(50),
    certifications JSONB DEFAULT '[]',
    disponibilite VARCHAR(50) DEFAULT 'immediate',
    date_disponibilite DATE,
    formats_acceptes JSONB DEFAULT '[]',
    taux_horaire_min NUMERIC(6,2),
    taux_horaire_souhaite NUMERIC(6,2),
    documents_complets BOOLEAN DEFAULT FALSE,
    derniere_verification_docs TIMESTAMP,
    score_completude INTEGER DEFAULT 0 CHECK (score_completude BETWEEN 0 AND 100),
    derniere_mise_a_jour TIMESTAMP,
    actif BOOLEAN DEFAULT TRUE,
    blackliste BOOLEAN DEFAULT FALSE,
    raison_blacklist TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_candidats_actif ON candidats(actif) WHERE actif = TRUE;
CREATE INDEX idx_candidats_disponibilite ON candidats(disponibilite);
CREATE INDEX idx_candidats_departement ON candidats(departement);
CREATE INDEX idx_candidats_metier ON candidats(metier_principal);
CREATE INDEX idx_candidats_competences ON candidats USING GIN (competences);
CREATE INDEX idx_candidats_nom_prenom ON candidats(nom, prenom);

-- Besoins
CREATE TABLE besoins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    id_externe VARCHAR(50),
    poste_recherche VARCHAR(200) NOT NULL,
    description TEXT,
    mission_type VARCHAR(50),
    ville VARCHAR(100),
    code_postal VARCHAR(10),
    departement VARCHAR(5),
    format_travail VARCHAR(50),
    horaires_details TEXT,
    date_debut DATE,
    date_fin DATE,
    duree_jours INTEGER,
    experience_requise_min NUMERIC(4,1),
    competences_requises JSONB DEFAULT '[]',
    certifications_requises JSONB DEFAULT '[]',
    permis_requis BOOLEAN DEFAULT FALSE,
    taux_horaire_min NUMERIC(6,2),
    taux_horaire_max NUMERIC(6,2),
    seuil_score_min INTEGER DEFAULT 40,
    nb_candidats_souhaites INTEGER DEFAULT 5,
    statut VARCHAR(30) DEFAULT 'ouvert' CHECK (statut IN ('ouvert', 'en_cours', 'pourvue', 'annule')),
    priorite VARCHAR(20) DEFAULT 'normale' CHECK (priorite IN ('haute', 'normale', 'basse')),
    nb_matchings INTEGER DEFAULT 0,
    meilleur_score NUMERIC(5,2),
    derniere_analyse TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_besoins_client ON besoins(client_id);
CREATE INDEX idx_besoins_statut ON besoins(statut);
CREATE INDEX idx_besoins_date_debut ON besoins(date_debut);
CREATE INDEX idx_besoins_departement ON besoins(departement);
CREATE INDEX idx_besoins_competences ON besoins USING GIN (competences_requises);

-- Matchings
CREATE TABLE matchings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    besoin_id UUID NOT NULL REFERENCES besoins(id) ON DELETE CASCADE,
    candidat_id UUID NOT NULL REFERENCES candidats(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    score_total NUMERIC(5,2) NOT NULL CHECK (score_total BETWEEN 0 AND 100),
    score_competences NUMERIC(5,2),
    score_localisation NUMERIC(5,2),
    score_disponibilite NUMERIC(5,2),
    score_financier NUMERIC(5,2),
    score_experience NUMERIC(5,2),
    explications JSONB DEFAULT '{}',
    points_forts JSONB DEFAULT '[]',
    points_faibles JSONB DEFAULT '[]',
    rang INTEGER,
    analyse_ia TEXT,
    utilise_ia BOOLEAN DEFAULT FALSE,
    vue BOOLEAN DEFAULT FALSE,
    date_vue TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(besoin_id, candidat_id)
);

CREATE INDEX idx_matchings_besoin ON matchings(besoin_id);
CREATE INDEX idx_matchings_candidat ON matchings(candidat_id);
CREATE INDEX idx_matchings_client ON matchings(client_id);
CREATE INDEX idx_matchings_score ON matchings(score_total DESC);
CREATE INDEX idx_matchings_rang ON matchings(besoin_id, rang);

-- Candidatures
CREATE TABLE candidatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    matching_id UUID REFERENCES matchings(id) ON DELETE SET NULL,
    besoin_id UUID NOT NULL REFERENCES besoins(id) ON DELETE CASCADE,
    candidat_id UUID NOT NULL REFERENCES candidats(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    nom_candidat VARCHAR(200),
    poste VARCHAR(200),
    score NUMERIC(5,2),
    statut VARCHAR(30) NOT NULL DEFAULT 'nouveau' CHECK (statut IN (
        'nouveau', 'shortliste', 'envoye_client', 'en_attente', 
        'selectionne', 'refuse', 'entretien_planifie', 'approuve', 
        'contrat_envoye', 'en_mission', 'desiste', 'mission_terminee'
    )),
    statut_precedent VARCHAR(30),
    date_shortlist TIMESTAMP,
    date_envoi_client TIMESTAMP,
    date_selection TIMESTAMP,
    date_entretien TIMESTAMP,
    date_debut_mission TIMESTAMP,
    date_fin_mission TIMESTAMP,
    lieu_entretien VARCHAR(200),
    notes_entretien TEXT,
    refuse BOOLEAN DEFAULT FALSE,
    raison_refus TEXT,
    refuse_par VARCHAR(20),
    desiste BOOLEAN DEFAULT FALSE,
    raison_desistement TEXT,
    date_desistement TIMESTAMP,
    taux_horaire_final NUMERIC(6,2),
    reference_contrat VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_candidatures_besoin ON candidatures(besoin_id);
CREATE INDEX idx_candidatures_candidat ON candidatures(candidat_id);
CREATE INDEX idx_candidatures_client ON candidatures(client_id);
CREATE INDEX idx_candidatures_statut ON candidatures(statut);
CREATE INDEX idx_candidatures_dates ON candidatures(date_envoi_client, date_selection);

-- Historique candidatures
CREATE TABLE historique_candidatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidature_id UUID NOT NULL REFERENCES candidatures(id) ON DELETE CASCADE,
    statut_avant VARCHAR(30),
    statut_apres VARCHAR(30) NOT NULL,
    commentaire TEXT,
    modifie_par UUID REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_historique_candidature ON historique_candidatures(candidature_id);
CREATE INDEX idx_historique_date ON historique_candidatures(created_at);

-- Timers
CREATE TABLE timers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidature_id UUID NOT NULL REFERENCES candidatures(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN (
        'relance_client_72h', 'entretien_rappel', 'debut_mission', 
        'fin_mission', 'renouvellement'
    )),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trigger_at TIMESTAMP NOT NULL,
    triggered_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    triggered BOOLEAN DEFAULT FALSE,
    cancelled BOOLEAN DEFAULT FALSE,
    action JSONB DEFAULT '{}'
);

CREATE INDEX idx_timers_candidature ON timers(candidature_id);
CREATE INDEX idx_timers_trigger ON timers(trigger_at) WHERE NOT triggered AND NOT cancelled;
CREATE INDEX idx_timers_actifs ON timers(candidature_id, type) WHERE NOT triggered AND NOT cancelled;

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidat_id UUID NOT NULL REFERENCES candidats(id) ON DELETE CASCADE,
    type VARCHAR(30) NOT NULL CHECK (type IN (
        'CV', 'CNI', 'TITRE_SEJOUR', 'PERMIS', 'RIB', 
        'CACES', 'DIPLOME', 'VISITE_MEDICALE', 'ATTESTATION', 'AUTRE'
    )),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    filepath VARCHAR(500) NOT NULL,
    mimetype VARCHAR(100),
    filesize INTEGER,
    date_expiration DATE,
    numero_document VARCHAR(100),
    verifie BOOLEAN DEFAULT FALSE,
    verifie_par UUID REFERENCES users(id) ON DELETE SET NULL,
    verifie_le TIMESTAMP,
    commentaire_verification TEXT,
    actif BOOLEAN DEFAULT TRUE,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_candidat ON documents(candidat_id);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_expiration ON documents(date_expiration) WHERE date_expiration IS NOT NULL;
CREATE INDEX idx_documents_verification ON documents(verifie, candidat_id);

-- Notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    candidature_id UUID REFERENCES candidatures(id) ON DELETE SET NULL,
    destinataire_email VARCHAR(255) NOT NULL,
    destinataire_type VARCHAR(20),
    template VARCHAR(50),
    sujet VARCHAR(255) NOT NULL,
    corps TEXT NOT NULL,
    variables JSONB DEFAULT '{}',
    attachments JSONB DEFAULT '[]',
    statut VARCHAR(20) DEFAULT 'pending' CHECK (statut IN ('pending', 'sent', 'failed', 'bounced', 'cancelled')),
    envoye_le TIMESTAMP,
    erreur TEXT,
    tentatives INTEGER DEFAULT 0,
    ouvert BOOLEAN DEFAULT FALSE,
    date_ouverture TIMESTAMP,
    clique BOOLEAN DEFAULT FALSE,
    date_clic TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_client ON notifications(client_id);
CREATE INDEX idx_notifications_candidature ON notifications(candidature_id);
CREATE INDEX idx_notifications_statut ON notifications(statut) WHERE statut = 'pending';
CREATE INDEX idx_notifications_destinataire ON notifications(destinataire_email);
CREATE INDEX idx_notifications_date ON notifications(created_at);

-- Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_token VARCHAR(500) UNIQUE NOT NULL,
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    refresh_expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_access_token ON sessions(access_token) WHERE NOT revoked;
CREATE INDEX idx_sessions_refresh_token ON sessions(refresh_token) WHERE NOT revoked;
CREATE INDEX idx_sessions_expires ON sessions(expires_at) WHERE NOT revoked;

-- Logs activite
CREATE TABLE logs_activite (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    ressource_type VARCHAR(50),
    ressource_id UUID,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_client ON logs_activite(client_id, created_at DESC);
CREATE INDEX idx_logs_user ON logs_activite(user_id, created_at DESC);
CREATE INDEX idx_logs_action ON logs_activite(action);
CREATE INDEX idx_logs_ressource ON logs_activite(ressource_type, ressource_id);

-- Triggers pour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_candidats_updated_at BEFORE UPDATE ON candidats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_besoins_updated_at BEFORE UPDATE ON besoins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_candidatures_updated_at BEFORE UPDATE ON candidatures
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Vues utiles
CREATE VIEW v_stats_clients AS
SELECT 
    c.id,
    c.nom_complet,
    COUNT(DISTINCT b.id) as nb_besoins,
    COUNT(DISTINCT m.id) as nb_matchings,
    COUNT(DISTINCT ca.id) as nb_candidatures,
    COUNT(DISTINCT ca.id) FILTER (WHERE ca.statut = 'en_mission') as nb_en_mission,
    AVG(m.score_total) as score_moyen
FROM clients c
LEFT JOIN besoins b ON c.id = b.client_id
LEFT JOIN matchings m ON b.id = m.besoin_id
LEFT JOIN candidatures ca ON m.id = ca.matching_id
WHERE c.actif = TRUE
GROUP BY c.id, c.nom_complet;

CREATE VIEW v_dashboard_candidats AS
SELECT 
    c.id,
    c.nom,
    c.prenom,
    c.email,
    c.disponibilite,
    c.score_completude,
    COUNT(DISTINCT m.id) as nb_matchings,
    MAX(m.score_total) as meilleur_score,
    COUNT(DISTINCT ca.id) as nb_candidatures,
    COUNT(DISTINCT ca.id) FILTER (WHERE ca.statut = 'en_mission') as en_mission
FROM candidats c
LEFT JOIN matchings m ON c.id = m.candidat_id
LEFT JOIN candidatures ca ON c.id = ca.candidat_id
WHERE c.actif = TRUE
GROUP BY c.id;