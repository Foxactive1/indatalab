"""
Configurações da aplicação InDataLab
Ambiente, banco de dados, uploads, Groq API
"""

import os
from datetime import timedelta


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)


class Config:
    """Configurações base para a aplicação"""
    
    # Flask
    SECRET_KEY = os.getenv(
        'SECRET_KEY',
        'indatalab-dev-secret-change-in-production'
    )
    
    # SQLAlchemy - no Android, certifica que o diretório instance existe
    instance_path = os.path.join(PROJECT_ROOT, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(instance_path, "indatalab.db")}'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload de arquivos
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
    # Garante que a pasta existe
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'csv', 'txt'}  # Inicialmente apenas CSV e TXT, pode expandir
    
    # Groq API - lê diretamente da variável de ambiente
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    GROQ_TIMEOUT = int(os.getenv('GROQ_TIMEOUT', 30))
    GROQ_MAX_TOKENS = int(os.getenv('GROQ_MAX_TOKENS', 2048))
    GROQ_TEMPERATURE = float(os.getenv('GROQ_TEMPERATURE', 0.7))
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    # Em produção, usar PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost/indatalab'
    )


class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Selector baseado em ENV
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

CURRENT_CONFIG = config_by_name[os.getenv('FLASK_ENV', 'development')]