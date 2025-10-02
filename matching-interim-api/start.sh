#!/bin/bash
# start.sh - Script de démarrage production

echo "🚀 Starting Matching Intérim API in production mode..."

# Variables d'environnement par défaut
export PYTHONUNBUFFERED=1
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-2}

# Vérifier la connexion DB
echo "📊 Checking database connection..."
python -c "
import os
import psycopg2
import sys
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

# Initialiser la base de données
echo "🔧 Initializing database..."
python init_db.py

# Lancer Gunicorn avec Uvicorn workers
echo "🎯 Starting Gunicorn with $WORKERS workers on port $PORT..."
exec gunicorn app.main:app \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance