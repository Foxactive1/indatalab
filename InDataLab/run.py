"""
InDataLab - Run Script
Inicializa a aplicação Flask
"""

import os
from dotenv import load_dotenv
from app import create_app, Config
from app.executor import kernel_manager

# Kernel manager ativa thread de cleanup automaticamente
# Pronto para usar!

# Carrega variáveis de ambiente do .env
load_dotenv('.env')

# Cria aplicação
app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Contexto para flask shell"""
    from app.models import (
        User, Notebook, Cell, Execution,
        Dataset, AIConversation
    )
    return {
        'db': db,
        'User': User,
        'Notebook': Notebook,
        'Cell': Cell,
        'Execution': Execution,
        'Dataset': Dataset,
        'AIConversation': AIConversation,
    }


if __name__ == '__main__':
    # Cria pastas necessárias
    os.makedirs('instance', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # Força debug=False no Android (Pydroid)
    # E desativa o reloader para evitar multiprocessing
    port = int(os.getenv('PORT', 5000))
    
    print(f"""
    
    ╔═══════════════════════════════════╗
    ║    InDataLab - ETAPA 1 - MVP      ║
    ║    Backend Consolidado            ║
    ╚═══════════════════════════════════╝
    
    Debug: False (forçado para Pydroid)
    Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}
    Groq Model: {app.config.get('GROQ_MODEL')}
    
    ▶ Servidor rodando em http://localhost:{port}
    
    """)
    
    app.run(
        debug=True,           # <-- MUDANÇA CRÍTICA
        use_reloader=False,    # <-- desliga recarregamento automático
        host='0.0.0.0',
        port=port,
    )