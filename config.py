"""
Configuration settings for the AI Job Application System
"""
import os
from datetime import timedelta

class Config:
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-key-change-in-production'
    
    # Database Settings - Azure SQL Database Configuration
    AZURE_SQL_SERVER = os.environ.get('AZURE_SQL_SERVER') or 'your-server-name.database.windows.net'
    AZURE_SQL_DATABASE = os.environ.get('AZURE_SQL_DATABASE') or 'recruitment_db'
    AZURE_SQL_USERNAME = os.environ.get('AZURE_SQL_USERNAME') or 'your-username'
    AZURE_SQL_PASSWORD = os.environ.get('AZURE_SQL_PASSWORD') or 'your-password'
    
    # Use SQLite for local development, Azure SQL for production
    USE_AZURE_SQL = os.environ.get('USE_AZURE_SQL', 'false').lower() == 'true'
    
    if USE_AZURE_SQL:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            f"mssql+pyodbc://{AZURE_SQL_USERNAME}:{AZURE_SQL_PASSWORD}@{AZURE_SQL_SERVER}:1433/{AZURE_SQL_DATABASE}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///recruitment.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # File Upload Settings - Use /tmp on Azure (writable), local folder otherwise
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    RESUME_FOLDER = os.path.join(UPLOAD_FOLDER, 'resumes')
    VIDEO_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    # AI/ML API Keys
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY') or 'your-groq-api-key'
    # Using llama-3.3-70b-versatile (llama3-70b-8192 was decommissioned)
    GROQ_MODEL = 'llama-3.3-70b-versatile'
    
    # Interview Settings
    SHORTLIST_THRESHOLD = 70  # Minimum resume score to shortlist
    QUESTIONS_PER_INTERVIEW = 10
    OTP_EXPIRY_HOURS = 48
    MAX_ANSWER_TIME_SECONDS = 120  # 2 minutes per question
    
    # Session Settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Email Settings (Optional - for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Analysis Weights (for final score calculation)
    WEIGHT_RESUME = 0.25
    WEIGHT_CONFIDENCE = 0.20
    WEIGHT_COMMUNICATION = 0.25
    WEIGHT_KNOWLEDGE = 0.30


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Force Azure SQL in production
    USE_AZURE_SQL = os.environ.get('USE_AZURE_SQL', 'true').lower() == 'true'
    
    # Production Database URI - build at class definition time from env vars
    _db_url = os.environ.get('DATABASE_URL')
    if _db_url:
        SQLALCHEMY_DATABASE_URI = _db_url
    elif USE_AZURE_SQL:
        _server = os.environ.get('AZURE_SQL_SERVER', 'your-server-name.database.windows.net')
        _database = os.environ.get('AZURE_SQL_DATABASE', 'recruitment_db')
        _username = os.environ.get('AZURE_SQL_USERNAME', '')
        _password = os.environ.get('AZURE_SQL_PASSWORD', '')
        SQLALCHEMY_DATABASE_URI = (
            f"mssql+pyodbc://{_username}:{_password}@{_server}:1433/{_database}"
            f"?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
        )
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///recruitment.db'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_recruitment.db'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
