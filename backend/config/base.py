import os
from datetime import timedelta

class BaseConfig:
    """Base configuration shared across all features"""
    
    # Flask Core
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'mysql+pymysql://mqc_user:mqc_password@localhost:3306/mqc_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG
    
    # Flask-SocketIO
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    SOCKETIO_ASYNC_MODE = 'eventlet'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    
    # Static Files
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)
    UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'static')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
