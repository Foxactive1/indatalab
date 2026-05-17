"""
Model: Cell
Representa células de código ou markdown dentro de um notebook
CORAÇÃO DO SISTEMA
"""

from datetime import datetime
from app.database.db import db


class Cell(db.Model):
    """
    Modelo de Célula (Code ou Markdown)
    
    Attributes:
        id: Identificador único
        notebook_id: Notebook que contém a célula
        cell_type: 'code' ou 'markdown'
        content: Código ou texto markdown
        output: Resultado da execução (para code cells)
        position: Ordem na sequência
        execution_count: Quantas vezes foi executada
        created_at: Data de criação
        updated_at: Última atualização
    """
    
    __tablename__ = 'cells'
    
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    notebook_id = db.Column(
        db.Integer,
        db.ForeignKey('notebooks.id'),
        nullable=False,
        index=True
    )
    
    cell_type = db.Column(
        db.String(50),
        nullable=False,
        default='code'
    )
    
    content = db.Column(
        db.Text,
        nullable=False
    )
    
    output = db.Column(
        db.Text
    )
    
    position = db.Column(
        db.Integer,
        default=0
    )
    
    execution_count = db.Column(
        db.Integer,
        default=0
    )
    
    is_hidden = db.Column(
        db.Boolean,
        default=False
    )
    
    tags = db.Column(
        db.Text
    )
    
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relacionamentos
    executions = db.relationship(
        'Execution',
        backref='cell',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f'<Cell {self.id} ({self.cell_type})>'
    
    def to_dict(self):
        """Serializar célula para JSON"""
        return {
            'id': self.id,
            'notebook_id': self.notebook_id,
            'cell_type': self.cell_type,
            'content': self.content,
            'output': self.output,
            'position': self.position,
            'execution_count': self.execution_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }