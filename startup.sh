#!/bin/bash

# Azure App Service Startup Script
# This runs every time the app starts on Azure

echo "=== Starting AI-Based Interview App ==="

# Install ODBC Driver for SQL Server (if using Azure SQL)
# Azure App Service Linux containers may not have it pre-installed
if ! odbcinst -q -d | grep -q "ODBC Driver 18 for SQL Server"; then
    echo "Installing ODBC Driver..."
    apt-get update -qq
    ACCEPT_EULA=Y apt-get install -y -qq msodbcsql18 unixodbc-dev 2>/dev/null || true
fi

# Download NLTK data
python -c "
import nltk
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
print('NLTK data downloaded.')
"

# Create upload directories
mkdir -p /home/site/wwwroot/uploads/resumes
mkdir -p /home/site/wwwroot/uploads/videos

# Run database migrations and seed if empty
python -c "
from app import create_app
from models import db, User
app = create_app('production')
with app.app_context():
    db.create_all()
    print('Database tables created/verified.')
    
    # Auto-seed if database is empty
    user_count = User.query.count()
    if user_count == 0:
        print('Database is empty, running seed...')
        from seed_database import seed
        seed()
    else:
        print(f'Database already has {user_count} users, skipping seed.')
"

# Start gunicorn - use Azure's PORT env variable (default 8000)
PORT=${PORT:-8000}
echo "Starting Gunicorn on port $PORT..."
gunicorn --bind=0.0.0.0:$PORT --timeout 600 --workers 2 --threads 4 app:app
