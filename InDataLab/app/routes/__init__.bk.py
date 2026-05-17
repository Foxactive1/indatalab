"""Routes package - Exporta todos os blueprints da API"""

from .notebooks_blueprint import notebooks_bp
from .cells_blueprint import cells_bp
from .executions_blueprint import executions_bp
from .copilot_blueprint import bp as copilot_bp   # <-- NOVO

__all__ = [
    'notebooks_bp',
    'cells_bp',
    'executions_bp',
    'copilot_bp'      # <-- NOVO
]