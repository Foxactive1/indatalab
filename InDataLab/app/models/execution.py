"""
Model: Execution
Registra cada execução de uma célula
Histórico, logs, erros, timing
"""

from datetime import datetime
from app.database.db import db


class Execution(db.Model):
    """
    Modelo de Execução
    
    Attributes:
        id: Identificador único
        cell_id: Célula que foi executada
        status: 'pending', 'running', 'success', 'error'
        execution_time: Tempo de execução em segundos
        logs: Saída padrão (stdout)
        error_message: Mensagem de erro
        executed_at: Quando foi executado
    """
    
    __tablename__ = 'executions'
    
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    cell_id = db.Column(
        db.Integer,
        db.ForeignKey('cells.id'),
        nullable=False,
        index=True
    )
    
    status = db.Column(
        db.String(20),
        default='pending',
        index=True
    )
    
    execution_time = db.Column(
        db.Float
    )
    
    logs = db.Column(
        db.Text
    )
    
    error_message = db.Column(
        db.Text
    )
    
    stderr = db.Column(
        db.Text
    )
    
    memory_used = db.Column(
        db.Float
    )
    
    executed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment='Quando foi executado'
    )
    
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='Data de registro'
    )
    
    def __repr__(self):
        return f'<Execution {self.id} ({self.status})>'
    
    def to_dict(self):
        """Serializar execução para JSON"""
        return {
            'id': self.id,
            'cell_id': self.cell_id,
            'status': self.status,
            'execution_time': self.execution_time,
            'logs': self.logs,
            'error_message': self.error_message,
            'executed_at': self.executed_at.isoformat(),
        }