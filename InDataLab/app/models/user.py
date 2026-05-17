"""
Model: User
Representa usuários da plataforma InDataLab
"""

from datetime import datetime
from app.database.db import db


class User(db.Model):
    """
    Modelo de usuário
    
    Attributes:
        id: Identificador único
        name: Nome do usuário
        email: Email único
        password_hash: Hash da senha (nunca armazenar senha em texto)
        created_at: Data de criação
        notebooks: Relacionamento com notebooks do usuário
    """
    
    __tablename__ = 'users'
    
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    name = db.Column(
        db.String(120),
        nullable=False
    )
    
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )
    
    password_hash = db.Column(
        db.Text,
        nullable=False
    )
    
    is_active = db.Column(
        db.Boolean,
        default=True
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
    notebooks = db.relationship(
        'Notebook',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    ai_conversations = db.relationship(
        'AIConversation',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Serializar usuário para JSON (sem senha)"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }