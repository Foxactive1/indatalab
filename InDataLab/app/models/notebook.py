"""
Model: Notebook
Representa notebooks (projetos) criados por usuários
Similar a Jupyter Notebooks
"""

from datetime import datetime
from app.database.db import db


class Notebook(db.Model):
    """
    Modelo de Notebook
    
    Attributes:
        id: Identificador único
        user_id: Usuário proprietário
        title: Título do notebook
        description: Descrição do notebook
        is_public: Se é visível publicamente
        created_at: Data de criação
        updated_at: Última atualização
        cells: Relacionamento com as células
    """
    
    __tablename__ = 'notebooks'
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='Identificador único do notebook'
    )
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    title = db.Column(
        db.String(255),
        nullable=False
    )
    
    description = db.Column(
        db.Text
    )
    
    is_public = db.Column(
        db.Boolean,
        default=False,
        index=True
    )
    
    is_archived = db.Column(
        db.Boolean,
        default=False
    )
    
    kernel_type = db.Column(
        db.String(50),
        default='python3'
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
    cells = db.relationship(
        'Cell',
        backref='notebook',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    datasets = db.relationship(
        'Dataset',
        backref='notebook',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f'<Notebook {self.title}>'
    
    def to_dict(self):
        """Serializar notebook para JSON"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'is_public': self.is_public,
            'kernel_type': self.kernel_type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'cell_count': len(self.cells),
        }