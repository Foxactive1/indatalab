"""
InDataLab - Aplicação Principal (ETAPA 2)
Factory Flask: Inicializa SQLAlchemy, Migrate, Models e registra Blueprints
"""

import os
from flask import Flask, jsonify, render_template
from .config import Config
from .database.db import db, migrate

from dotenv import load_dotenv
load_dotenv(".env")  # carrega variáveis de ambiente


def create_app(config_class=Config):
    """
    Factory para criar e configurar a aplicação Flask
    
    Responsabilidades:
    1. Criar instância Flask
    2. Carregar configurações
    3. Inicializar extensões (db, migrate)
    4. Criar diretório instance e uploads se necessário
    5. Criar tabelas (desenvolvimento)
    6. Registrar blueprints (rotas)
    7. Registrar handlers (erros)
    
    Returns:
        Flask app instance totalmente configurada
    """
    
    # 1️⃣ Criar instância Flask
    app = Flask(__name__)
    
    # 2️⃣ Carregar configurações
    app.config.from_object(config_class)
    
    # 3️⃣ Garantir que o diretório de banco de dados existe (para SQLite)
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '', 1)
        if not os.path.isabs(db_path):
            db_path = os.path.join(app.instance_path, db_path)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    # 4️⃣ Garantir que o diretório de uploads existe
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)
    
    # 5️⃣ Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 6️⃣ Contexto da aplicação: imports e tabelas
    with app.app_context():
        # Importa todos os modelos (necessário para o Migrate e criação de tabelas)
        from .models import (
            user,
            notebook,
            cell,
            execution,
            dataset,
            ai_conversation
        )
        
        # Cria tabelas se não existirem (modo desenvolvimento)
        db.create_all()
    
    # 7️⃣ Registrar blueprints (rotas)
    from .routes import (
        notebooks_bp,
        cells_bp,
        executions_bp,
        copilot_bp,
        datasets_bp      # <-- AGORA IMPORTADO DO __init__.py DE ROUTES
    )
    
    app.register_blueprint(notebooks_bp)
    app.register_blueprint(cells_bp)
    app.register_blueprint(executions_bp)
    app.register_blueprint(copilot_bp)
    app.register_blueprint(datasets_bp)   # <-- REGISTRO ADICIONADO
    
    # 8️⃣ Rotas e Handlers
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "InDataLab API",
            "version": "0.2.0",
            "environment": app.config.get('FLASK_ENV', 'development')
        }), 200
    
    @app.route('/')
    def index():
        """Página principal - Frontend"""
        return render_template('index.html')
    
    @app.errorhandler(404)
    def not_found(error):
        """Handler: 404 Not Found"""
        return jsonify({
            "success": False,
            "error": "Rota não encontrada",
            "status_code": 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handler: 500 Internal Server Error"""
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Erro interno do servidor",
            "status_code": 500
        }), 500
    
    return app