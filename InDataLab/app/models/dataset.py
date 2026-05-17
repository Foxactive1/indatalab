"""
Model: Dataset
Representa arquivos e datasets armazenados/processados
Suporta CSV, JSON, Excel, Parquet, etc
"""

from datetime import datetime
from app.database.db import db


class Dataset(db.Model):
    """
    Modelo de Dataset
    
    Attributes:
        id: Identificador único
        notebook_id: Notebook associado
        filename: Nome do arquivo
        file_type: Tipo (csv, json, xlsx, parquet, etc)
        file_path: Caminho no servidor
        file_size: Tamanho em bytes
        rows: Número de linhas (se aplicável)
        columns: Número de colunas (se aplicável)
        created_at: Data de upload
    """
    
    __tablename__ = 'datasets'
    
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
    
    filename = db.Column(
        db.String(255),
        nullable=False
    )
    
    file_type = db.Column(
        db.String(20),
        nullable=False
    )
    
    file_path = db.Column(
        db.Text,
        nullable=False
    )
    
    file_size = db.Column(
        db.BigInteger
    )
    
    rows = db.Column(
        db.Integer
    )
    
    columns = db.Column(
        db.Integer
    )
    
    column_names = db.Column(
        db.Text
    )
    
    description = db.Column(
        db.Text
    )
    
    is_public = db.Column(
        db.Boolean,
        default=False
    )
    
    extra_metadata = db.Column(
        db.Text,
        comment='Metadados adicionais em formato JSON'
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
    
    def __repr__(self):
        return f'<Dataset {self.filename}>'
    
    def to_dict(self):
        """Serializar dataset para JSON"""
        return {
            'id': self.id,
            'notebook_id': self.notebook_id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'rows': self.rows,
            'columns': self.columns,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
        }