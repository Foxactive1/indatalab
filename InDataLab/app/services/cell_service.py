"""
Service: CellService
CRUD de células com validação, ordenação e execução
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from app.database.db import db
from app.models.cell import Cell
from app.models.notebook import Notebook


class CellService:
    """
    Serviço para operações com Células
    
    Garante:
    - Validação de conteúdo
    - Autorização (notebook pertence ao user)
    - Ordenação automática (position)
    - Segurança de tipo (code ou markdown)
    """
    
    @staticmethod
    def _validate_user_owns_notebook(notebook_id: int, user_id: int) -> bool:
        """Validar se notebook pertence ao usuário"""
        notebook = Notebook.query.filter_by(
            id=notebook_id,
            user_id=user_id
        ).first()
        return notebook is not None
    
    @staticmethod
    def create_cell(
        notebook_id: int,
        user_id: int,
        cell_type: str,
        content: str,
        position: Optional[int] = None,
        tags: Optional[str] = None
    ) -> Tuple[Optional[Cell], Optional[str]]:
        """
        Criar nova célula
        
        Args:
            notebook_id: ID do notebook
            user_id: ID do usuário (validação)
            cell_type: 'code' ou 'markdown'
            content: Conteúdo
            position: Posição (se None, vai para fim)
            tags: Tags separadas por vírgula
        
        Returns:
            (Cell, None) ou (None, mensagem_erro)
        """
        
        try:
            # Validar autorização
            if not CellService._validate_user_owns_notebook(notebook_id, user_id):
                return None, "Sem permissão"
            
            # Validar tipo
            if cell_type not in ['code', 'markdown']:
                return None, "cell_type deve ser 'code' ou 'markdown'"
            
            # Validar conteúdo
            if not content or len(content.strip()) == 0:
                return None, "Conteúdo é obrigatório"
            
            # Determinar posição
            if position is None:
                # Contar células existentes
                max_pos = db.session.query(
                    db.func.max(Cell.position)
                ).filter_by(notebook_id=notebook_id).scalar() or -1
                position = max_pos + 1
            
            # Criar
            cell = Cell(
                notebook_id=notebook_id,
                cell_type=cell_type,
                content=content.strip(),
                position=position,
                tags=tags.strip() if tags else None,
                execution_count=0
            )
            
            db.session.add(cell)
            db.session.commit()
            
            return cell, None
        
        except Exception as e:
            db.session.rollback()
            return None, f"Erro ao criar célula: {str(e)}"
    
    @staticmethod
    def get_cell(
        cell_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Cell]:
        """
        Buscar célula por ID
        
        Args:
            cell_id: ID da célula
            user_id: Se passar, valida permissão
        
        Returns:
            Cell ou None
        """
        
        cell = Cell.query.get(cell_id)
        
        if not cell:
            return None
        
        # Validar autorização se user_id fornecido
        if user_id:
            notebook = Notebook.query.get(cell.notebook_id)
            if not notebook or notebook.user_id != user_id:
                return None
        
        return cell
    
    @staticmethod
    def list_cells(
        notebook_id: int,
        user_id: int,
        cell_type: Optional[str] = None
    ) -> Tuple[Optional[List[Cell]], Optional[str]]:
        """
        Listar células de um notebook (ordenadas por position)
        
        Args:
            notebook_id: ID do notebook
            user_id: ID do usuário (validação)
            cell_type: Filtro por tipo ('code', 'markdown')
        
        Returns:
            (cells, None) ou (None, mensagem_erro)
        """
        
        try:
            # Validar autorização
            if not CellService._validate_user_owns_notebook(notebook_id, user_id):
                return None, "Sem permissão"
            
            query = Cell.query.filter_by(notebook_id=notebook_id)
            
            if cell_type:
                if cell_type not in ['code', 'markdown']:
                    return None, "cell_type inválido"
                query = query.filter_by(cell_type=cell_type)
            
            cells = query.order_by(Cell.position.asc()).all()
            
            return cells, None
        
        except Exception as e:
            return None, f"Erro ao listar: {str(e)}"
    
    @staticmethod
    def update_cell(
        cell_id: int,
        user_id: int,
        **kwargs
    ) -> Tuple[Optional[Cell], Optional[str]]:
        """
        Atualizar célula
        
        Campos atualizáveis:
        - content
        - cell_type (cuidado!)
        - output
        - position
        - is_hidden
        - tags
        
        Args:
            cell_id: ID da célula
            user_id: ID do usuário (validação)
            **kwargs: Campos a atualizar
        
        Returns:
            (Cell, None) ou (None, mensagem_erro)
        """
        
        try:
            cell = CellService.get_cell(cell_id, user_id)
            
            if not cell:
                return None, "Célula não encontrada ou sem permissão"
            
            # Campos permitidos
            allowed_fields = {
                'content', 'cell_type', 'output',
                'position', 'is_hidden', 'tags'
            }
            
            for field, value in kwargs.items():
                if field not in allowed_fields:
                    continue
                
                # Validar conteúdo
                if field == 'content':
                    if not value or len(value.strip()) == 0:
                        return None, "Conteúdo é obrigatório"
                    value = value.strip()
                
                # Validar tipo
                if field == 'cell_type':
                    if value not in ['code', 'markdown']:
                        return None, "cell_type inválido"
                
                # Validar posição
                if field == 'position':
                    if not isinstance(value, int) or value < 0:
                        return None, "position inválida"
                
                setattr(cell, field, value)
            
            cell.updated_at = datetime.utcnow()
            db.session.commit()
            
            return cell, None
        
        except Exception as e:
            db.session.rollback()
            return None, f"Erro ao atualizar: {str(e)}"
    
    @staticmethod
    def delete_cell(
        cell_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Deletar célula
        
        Args:
            cell_id: ID da célula
            user_id: ID do usuário (validação)
        
        Returns:
            (sucesso, mensagem_erro)
        """
        
        try:
            cell = CellService.get_cell(cell_id, user_id)
            
            if not cell:
                return False, "Célula não encontrada ou sem permissão"
            
            # Reordenar células após (position < current)
            notebook_id = cell.notebook_id
            current_pos = cell.position
            
            db.session.delete(cell)
            db.session.commit()
            
            # Renumerar posições
            cells_after = Cell.query.filter(
                Cell.notebook_id == notebook_id,
                Cell.position > current_pos
            ).all()
            
            for idx, c in enumerate(cells_after, start=current_pos):
                c.position = idx
            
            db.session.commit()
            
            return True, None
        
        except Exception as e:
            db.session.rollback()
            return False, f"Erro ao deletar: {str(e)}"
    
    @staticmethod
    def reorder_cells(
        notebook_id: int,
        user_id: int,
        cell_order: List[int]  # [cell_id, cell_id, ...]
    ) -> Tuple[bool, Optional[str]]:
        """
        Reordenar células (via arrastar, por exemplo)
        
        Args:
            notebook_id: ID do notebook
            user_id: ID do usuário (validação)
            cell_order: Lista de IDs em nova ordem
        
        Returns:
            (sucesso, mensagem_erro)
        """
        
        try:
            # Validar autorização
            if not CellService._validate_user_owns_notebook(notebook_id, user_id):
                return False, "Sem permissão"
            
            # Validar que todas as células existem
            cells_dict = {}
            for cell_id in cell_order:
                cell = Cell.query.filter_by(
                    id=cell_id,
                    notebook_id=notebook_id
                ).first()
                if not cell:
                    return False, f"Célula {cell_id} não encontrada"
                cells_dict[cell_id] = cell
            
            # Atualizar posições
            for new_pos, cell_id in enumerate(cell_order):
                cells_dict[cell_id].position = new_pos
            
            db.session.commit()
            
            return True, None
        
        except Exception as e:
            db.session.rollback()
            return False, f"Erro ao reordenar: {str(e)}"
    
    @staticmethod
    def increment_execution_count(cell_id: int) -> bool:
        """
        Incrementar execution_count (chamado após execução)
        
        Args:
            cell_id: ID da célula
        
        Returns:
            Sucesso
        """
        
        try:
            cell = Cell.query.get(cell_id)
            if cell:
                cell.execution_count += 1
                db.session.commit()
                return True
            return False
        except:
            db.session.rollback()
            return False
