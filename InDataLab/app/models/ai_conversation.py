"""
Model: AIConversation
Histórico de conversas com Groq API
Integrado ao contexto do notebook/célula
"""

from datetime import datetime
from app.database.db import db


class AIConversation(db.Model):
    """
    Modelo de Conversa com IA
    
    Attributes:
        id: Identificador único
        user_id: Usuário
        notebook_id: Notebook associado (opcional)
        cell_id: Célula associada (opcional)
        role: 'user' ou 'assistant'
        content: Mensagem
        model: Modelo Groq usado
        tokens_used: Tokens consumidos
        temperature: Temperature usado
        created_at: Quando foi enviado
    """
    
    __tablename__ = 'ai_conversations'
    
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    notebook_id = db.Column(
        db.Integer,
        db.ForeignKey('notebooks.id', ondelete='SET NULL')
    )
    
    cell_id = db.Column(
        db.Integer,
        db.ForeignKey('cells.id', ondelete='SET NULL')
    )
    
    conversation_session_id = db.Column(
        db.String(100),
        index=True
    )
    
    role = db.Column(
        db.String(20),
        nullable=False,
        default='user',
        index=True
    )
    
    content = db.Column(
        db.Text,
        nullable=False
    )
    
    model = db.Column(
        db.String(100),
        default='llama-3.3-70b-versatile'
    )
    
    temperature = db.Column(
        db.Float,
        default=0.7
    )
    
    tokens_used = db.Column(
        db.Integer
    )
    
    input_tokens = db.Column(
        db.Integer
    )
    
    output_tokens = db.Column(
        db.Integer
    )
    
    processing_time = db.Column(
        db.Float
    )
    
    groq_request_id = db.Column(
        db.String(100)
    )
    
    extra_metadata = db.Column(
        db.Text,
        comment='Metadados adicionais da conversa'
    )
    
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self):
        return f'<AIConversation {self.id} ({self.role})>'
    
    def to_dict(self):
        """Serializar conversa para JSON"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notebook_id': self.notebook_id,
            'cell_id': self.cell_id,
            'role': self.role,
            'content': self.content,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat(),
        }