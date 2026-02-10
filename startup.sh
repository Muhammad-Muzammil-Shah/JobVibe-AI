#!/bin/bash

# Azure App Service Startup Script
# This runs every time the app starts on Azure

echo "=== Starting AI-Based Interview App ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version 2>&1)"
echo "PORT: ${PORT:-8000}"

# Install FFmpeg (required for video/audio processing)
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing FFmpeg..."
    apt-get update -qq
    apt-get install -y -qq ffmpeg 2>/dev/null || true
fi

# Install ODBC Driver for SQL Server (if using Azure SQL)
# Azure App Service Linux containers may not have it pre-installed
if ! odbcinst -q -d 2>/dev/null | grep -q "ODBC Driver 18 for SQL Server"; then
    echo "Installing ODBC Driver..."
    apt-get update -qq 2>/dev/null || true
    # Add Microsoft repository if not present
    if [ ! -f /etc/apt/sources.list.d/mssql-release.list ]; then
        curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg 2>/dev/null || true
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list 2>/dev/null || true
        apt-get update -qq 2>/dev/null || true
    fi
    ACCEPT_EULA=Y apt-get install -y -qq msodbcsql18 unixodbc-dev 2>/dev/null || echo "ODBC driver install skipped (may already be available)"
fi

# Download NLTK data
echo "Downloading NLTK data..."
python -c "
import nltk
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    print('NLTK data downloaded.')
except Exception as e:
    print(f'NLTK download warning: {e}')
" || echo "NLTK download skipped"

# Create upload directories
mkdir -p /home/site/wwwroot/uploads/resumes
mkdir -p /home/site/wwwroot/uploads/videos

# Run database migrations and seed if empty
echo "Initializing database..."
python -c "
import sys
try:
    from app import app
    from models import db, User
    with app.app_context():
        db.create_all()
        print('Database tables created/verified.')
        
        # Auto-seed if database is empty
        try:
            user_count = User.query.count()
            if user_count == 0:
                print('Database is empty, running seed...')
                from seed_database import seed
                seed()
            else:
                print(f'Database already has {user_count} users, skipping seed.')
        except Exception as e:
            print(f'Seed check warning: {e}')
except Exception as e:
    print(f'Database initialization error: {e}')
    print('Continuing without database init - Gunicorn will retry on first request')
" || echo "Database init will be attempted by the app"

# Start gunicorn - use Azure's PORT env variable (default 8000)
PORT=${PORT:-8000}
echo "Starting Gunicorn on port $PORT..."
gunicorn --bind=0.0.0.0:$PORT --timeout 600 --workers 2 --threads 4 app:app
