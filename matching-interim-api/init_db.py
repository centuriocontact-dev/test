#!/usr/bin/env python3
"""
init_db.py - Script d'initialisation de la base de données
Idempotent : peut être exécuté plusieurs fois sans problème
"""

import os
import sys
import logging
from datetime import datetime
import secrets
from pathlib import Path

# Ajouter le path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialiser la base de données avec les tables et données de base"""
    
    try:
        # Imports après avoir configuré le path
        from app.database import engine, SessionLocal
        from app.models.models import Base, Client, User
        from app.core.security import get_password_hash
        
        logger.info("🔧 Initializing database...")
        
        # Créer toutes les tables
        logger.info("📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created successfully")
        
        # Créer une session
        db = SessionLocal()
        
        try:
            # Vérifier si le client admin existe déjà
            admin_client = db.query(Client).filter(
                Client.code == os.getenv('ADMIN_CLIENT_CODE', 'ADMIN')
            ).first()
            
            if not admin_client:
                logger.info("👤 Creating admin client...")
                
                # Créer le client admin
                admin_client = Client(
                    code=os.getenv('ADMIN_CLIENT_CODE', 'ADMIN'),
                    nom_complet="Administration",
                    email_contact=os.getenv('ADMIN_EMAIL', 'admin@matching-interim.com'),
                    plan='premium',
                    max_besoins=1000,
                    max_candidats=10000,
                    actif=True,
                    config={
                        'features': {
                            'ai_matching': True,
                            'export_excel': True,
                            'api_access': True
                        }
                    }
                )
                db.add(admin_client)
                db.commit()
                db.refresh(admin_client)
                logger.info(f"✅ Admin client created: {admin_client.code}")
            else:
                logger.info(f"ℹ️ Admin client already exists: {admin_client.code}")
            
            # Vérifier si l'utilisateur admin existe
            admin_user = db.query(User).filter(
                User.email == os.getenv('ADMIN_EMAIL', 'admin@matching-interim.com')
            ).first()
            
            if not admin_user:
                logger.info("👤 Creating admin user...")
                
                # Mot de passe admin (à changer après première connexion)
                admin_password = os.getenv('ADMIN_PASSWORD', 'ChangeMe123!')
                
                admin_user = User(
                    client_id=admin_client.id,
                    email=os.getenv('ADMIN_EMAIL', 'admin@matching-interim.com'),
                    password_hash=get_password_hash(admin_password),
                    nom="Admin",
                    prenom="System",
                    role="admin",
                    permissions=["*"],  # Toutes les permissions
                    email_verified=True,
                    actif=True
                )
                db.add(admin_user)
                db.commit()
                
                logger.info(f"✅ Admin user created: {admin_user.email}")
                logger.warning(f"⚠️  DEFAULT PASSWORD: {admin_password}")
                logger.warning("⚠️  CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!")
            else:
                logger.info(f"ℹ️ Admin user already exists: {admin_user.email}")
            
            # Créer un client de démonstration (optionnel)
            demo_client = db.query(Client).filter(
                Client.code == "DEMO"
            ).first()
            
            if not demo_client:
                logger.info("🎯 Creating demo client...")
                
                demo_client = Client(
                    code="DEMO",
                    nom_complet="Client Démonstration",
                    email_contact="demo@matching-interim.com",
                    plan='standard',
                    max_besoins=10,
                    max_candidats=100,
                    actif=True
                )
                db.add(demo_client)
                
                # Utilisateur démo
                demo_user = User(
                    client_id=demo_client.id,
                    email="demo@matching-interim.com",
                    password_hash=get_password_hash("Demo123!"),
                    nom="Demo",
                    prenom="User",
                    role="user",
                    email_verified=True,
                    actif=True
                )
                db.add(demo_user)
                db.commit()
                
                logger.info("✅ Demo client and user created")
                logger.info("   Email: demo@matching-interim.com")
                logger.info("   Password: Demo123!")
            
            # Afficher les statistiques
            client_count = db.query(Client).count()
            user_count = db.query(User).count()
            
            logger.info("\n📊 Database Statistics:")
            logger.info(f"   Clients: {client_count}")
            logger.info(f"   Users: {user_count}")
            
            logger.info("\n✅ Database initialization completed successfully!")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)

def check_environment():
    """Vérifier les variables d'environnement nécessaires"""
    
    required_vars = ['DATABASE_URL', 'SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("💡 Copy .env.production.example to .env and fill in the values")
        sys.exit(1)
    
    # Avertir si des valeurs par défaut sont utilisées
    if os.getenv('SECRET_KEY') == 'CHANGEME_USE_SECURE_RANDOM_KEY_IN_PRODUCTION':
        logger.warning("⚠️  Using default SECRET_KEY - CHANGE THIS IN PRODUCTION!")
    
    if os.getenv('ADMIN_PASSWORD') == 'ChangeMe123!':
        logger.warning("⚠️  Using default admin password - CHANGE THIS IMMEDIATELY!")

if __name__ == "__main__":
    logger.info("🚀 Matching Intérim API - Database Initialization")
    logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier l'environnement
    check_environment()
    
    # Initialiser la base
    init_database()