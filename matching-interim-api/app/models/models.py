# models.py
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Numeric, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, declarative_base
import uuid

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    nom_complet = Column(String(200), nullable=False)
    logo = Column(String(10))
    couleur = Column(String(7))
    email_contact = Column(String(255))
    telephone = Column(String(20))
    config = Column(JSONB, default={})
    plan = Column(String(50), default='standard')
    max_besoins = Column(Integer, default=10)
    max_candidats = Column(Integer, default=100)
    actif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="client", cascade="all, delete-orphan")
    besoins = relationship("Besoin", back_populates="client", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nom = Column(String(100))
    prenom = Column(String(100))
    telephone = Column(String(20))
    role = Column(String(20), default='user', nullable=False)
    permissions = Column(JSONB, default=[])
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    actif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship("Client", back_populates="users")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

class Candidat(Base):
    __tablename__ = 'candidats'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_externe = Column(String(50))
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255))
    telephone = Column(String(20))
    date_naissance = Column(Date)
    code_postal = Column(String(10))
    ville = Column(String(100))
    departement = Column(String(5))
    mobilite_km = Column(Integer, default=30)
    permis_conduire = Column(Boolean, default=False)
    vehicule = Column(Boolean, default=False)
    experience_annees = Column(Numeric(4, 1))
    metier_principal = Column(String(100))
    competences = Column(JSONB, default=[])
    niveau_etude = Column(String(50))
    certifications = Column(JSONB, default=[])
    disponibilite = Column(String(50), default='immediate')
    date_disponibilite = Column(Date)
    formats_acceptes = Column(JSONB, default=[])
    taux_horaire_min = Column(Numeric(6, 2))
    taux_horaire_souhaite = Column(Numeric(6, 2))
    documents_complets = Column(Boolean, default=False)
    derniere_verification_docs = Column(DateTime)
    score_completude = Column(Integer, default=0)
    derniere_mise_a_jour = Column(DateTime)
    actif = Column(Boolean, default=True)
    blackliste = Column(Boolean, default=False)
    raison_blacklist = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    matchings = relationship("Matching", back_populates="candidat", cascade="all, delete-orphan")
    candidatures = relationship("Candidature", back_populates="candidat", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="candidat", cascade="all, delete-orphan")

class Besoin(Base):
    __tablename__ = 'besoins'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    id_externe = Column(String(50))
    poste_recherche = Column(String(200), nullable=False)
    description = Column(Text)
    mission_type = Column(String(50))
    ville = Column(String(100))
    code_postal = Column(String(10))
    departement = Column(String(5))
    format_travail = Column(String(50))
    horaires_details = Column(Text)
    date_debut = Column(Date)
    date_fin = Column(Date)
    duree_jours = Column(Integer)
    experience_requise_min = Column(Numeric(4, 1))
    competences_requises = Column(JSONB, default=[])
    certifications_requises = Column(JSONB, default=[])
    permis_requis = Column(Boolean, default=False)
    taux_horaire_min = Column(Numeric(6, 2))
    taux_horaire_max = Column(Numeric(6, 2))
    seuil_score_min = Column(Integer, default=40)
    nb_candidats_souhaites = Column(Integer, default=5)
    statut = Column(String(30), default='ouvert')
    priorite = Column(String(20), default='normale')
    nb_matchings = Column(Integer, default=0)
    meilleur_score = Column(Numeric(5, 2))
    derniere_analyse = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship("Client", back_populates="besoins")
    matchings = relationship("Matching", back_populates="besoin", cascade="all, delete-orphan")
    candidatures = relationship("Candidature", back_populates="besoin", cascade="all, delete-orphan")

class Matching(Base):
    __tablename__ = 'matchings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    besoin_id = Column(UUID(as_uuid=True), ForeignKey('besoins.id', ondelete='CASCADE'), nullable=False)
    candidat_id = Column(UUID(as_uuid=True), ForeignKey('candidats.id', ondelete='CASCADE'), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    score_total = Column(Numeric(5, 2), nullable=False)
    score_competences = Column(Numeric(5, 2))
    score_localisation = Column(Numeric(5, 2))
    score_disponibilite = Column(Numeric(5, 2))
    score_financier = Column(Numeric(5, 2))
    score_experience = Column(Numeric(5, 2))
    explications = Column(JSONB, default={})
    points_forts = Column(JSONB, default=[])
    points_faibles = Column(JSONB, default=[])
    rang = Column(Integer)
    analyse_ia = Column(Text)
    utilise_ia = Column(Boolean, default=False)
    vue = Column(Boolean, default=False)
    date_vue = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    besoin = relationship("Besoin", back_populates="matchings")
    candidat = relationship("Candidat", back_populates="matchings")
    candidature = relationship("Candidature", back_populates="matching", uselist=False)

class Candidature(Base):
    __tablename__ = 'candidatures'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matching_id = Column(UUID(as_uuid=True), ForeignKey('matchings.id', ondelete='SET NULL'))
    besoin_id = Column(UUID(as_uuid=True), ForeignKey('besoins.id', ondelete='CASCADE'), nullable=False)
    candidat_id = Column(UUID(as_uuid=True), ForeignKey('candidats.id', ondelete='CASCADE'), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    nom_candidat = Column(String(200))
    poste = Column(String(200))
    score = Column(Numeric(5, 2))
    statut = Column(String(30), default='nouveau', nullable=False)
    statut_precedent = Column(String(30))
    date_shortlist = Column(DateTime)
    date_envoi_client = Column(DateTime)
    date_selection = Column(DateTime)
    date_entretien = Column(DateTime)
    date_debut_mission = Column(DateTime)
    date_fin_mission = Column(DateTime)
    lieu_entretien = Column(String(200))
    notes_entretien = Column(Text)
    refuse = Column(Boolean, default=False)
    raison_refus = Column(Text)
    refuse_par = Column(String(20))
    desiste = Column(Boolean, default=False)
    raison_desistement = Column(Text)
    date_desistement = Column(DateTime)
    taux_horaire_final = Column(Numeric(6, 2))
    reference_contrat = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    matching = relationship("Matching", back_populates="candidature")
    besoin = relationship("Besoin", back_populates="candidatures")
    candidat = relationship("Candidat", back_populates="candidatures")
    historique = relationship("HistoriqueCandidature", back_populates="candidature", cascade="all, delete-orphan")
    timers = relationship("Timer", back_populates="candidature", cascade="all, delete-orphan")

class HistoriqueCandidature(Base):
    __tablename__ = 'historique_candidatures'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidature_id = Column(UUID(as_uuid=True), ForeignKey('candidatures.id', ondelete='CASCADE'), nullable=False)
    statut_avant = Column(String(30))
    statut_apres = Column(String(30), nullable=False)
    commentaire = Column(Text)
    modifie_par = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    candidature = relationship("Candidature", back_populates="historique")

class Timer(Base):
    __tablename__ = 'timers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidature_id = Column(UUID(as_uuid=True), ForeignKey('candidatures.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    trigger_at = Column(DateTime, nullable=False)
    triggered_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    triggered = Column(Boolean, default=False)
    cancelled = Column(Boolean, default=False)
    action = Column(JSONB, default={})
    
    candidature = relationship("Candidature", back_populates="timers")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidat_id = Column(UUID(as_uuid=True), ForeignKey('candidats.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(30), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    filepath = Column(String(500), nullable=False)
    mimetype = Column(String(100))
    filesize = Column(Integer)
    date_expiration = Column(Date)
    numero_document = Column(String(100))
    verifie = Column(Boolean, default=False)
    verifie_par = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    verifie_le = Column(DateTime)
    commentaire_verification = Column(Text)
    actif = Column(Boolean, default=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    candidat = relationship("Candidat", back_populates="documents")

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    candidature_id = Column(UUID(as_uuid=True), ForeignKey('candidatures.id', ondelete='SET NULL'))
    destinataire_email = Column(String(255), nullable=False)
    destinataire_type = Column(String(20))
    template = Column(String(50))
    sujet = Column(String(255), nullable=False)
    corps = Column(Text, nullable=False)
    variables = Column(JSONB, default={})
    attachments = Column(JSONB, default=[])
    statut = Column(String(20), default='pending')
    envoye_le = Column(DateTime)
    erreur = Column(Text)
    tentatives = Column(Integer, default=0)
    ouvert = Column(Boolean, default=False)
    date_ouverture = Column(DateTime)
    clique = Column(Boolean, default=False)
    date_clic = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    access_token = Column(String(500), unique=True, nullable=False)
    refresh_token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime, nullable=False)
    ip_address = Column(INET)
    user_agent = Column(Text)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")

class LogActivite(Base):
    __tablename__ = 'logs_activite'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    action = Column(String(100), nullable=False)
    ressource_type = Column(String(50))
    ressource_id = Column(UUID(as_uuid=True))
    description = Column(Text)
    metadata = Column(JSONB, default={})
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)