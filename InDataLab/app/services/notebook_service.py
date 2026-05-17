"""
Service: NotebookService
CRUD de notebooks com validação e autorização
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from app.database.db import db
from app.models.notebook import Notebook
from app.models.cell import Cell


class NotebookService:
    """
    Serviço para operações com Notebooks
    
    Garante:
    - Validação de entrada
    - Autorização (user owns notebook)
    - Relacionamentos corretos
    - Semântica de negócio
    """
    
    @staticmethod
    def create_notebook(
        user_id: int,
        title: str,
        description: Optional[str] = None,
        is_public: bool = False,
        kernel_type: str = 'python3'
    ) -> Tuple[Optional[Notebook], Optional[str]]:
        """
        Criar novo notebook
        
        Args:
            user_id: ID do usuário
            title: Título (obrigatório)
            description: Descrição
            is_public: Visibilidade
            kernel_type: Tipo de kernel
        
        Returns:
            (Notebook, None) ou (None, mensagem_erro)
        """
        
        try:
            # Validação
            if not title or len(title.strip()) == 0:
                return None, "Título é obrigatório"
            
            if len(title) > 255:
                return None, "Título muito longo (máx 255 caracteres)"
            
            # Criar
            notebook = Notebook(
                user_id=user_id,
                title=title.strip(),
                description=description.strip() if description else None,
                is_public=is_public,
                kernel_type=kernel_type
            )
            
            db.session.add(notebook)
            db.session.commit()
            
            return notebook, None
        
        except Exception as e:
            db.session.rollback()
            return None, f"Erro ao criar notebook: {str(e)}"
    
    @staticmethod
    def get_notebook(
        notebook_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Notebook]:
        """
        Buscar notebook por ID
        
        Args:
            notebook_id: ID do notebook
            user_id: Se passar, valida se pertence ao usuário
        
        Returns:
            Notebook ou None
        """
        
        notebook = Notebook.query.get(notebook_id)
        
        if not notebook:
            return None
        
        # Validar autorização se user_id fornecido
        if user_id and notebook.user_id != user_id:
            return None
        
        return notebook
    
    @staticmethod
    def list_notebooks(
        user_id: int,
        is_archived: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Notebook], int, int]:
        """
        Listar notebooks do usuário (paginado)
        
        Args:
            user_id: ID do usuário
            is_archived: Filtro por arquivo
            page: Página (1-indexed)
            per_page: Notebooks por página
        
        Returns:
            (notebooks, total, páginas)
        """
        
        query = Notebook.query.filter_by(user_id=user_id)
        
        if is_archived is not None:
            query = query.filter_by(is_archived=is_archived)
        
        # Paginação
        pagination = query.order_by(
            Notebook.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return pagination.items, pagination.total, pagination.pages
    
    @staticmethod
    def update_notebook(
        notebook_id: int,
        user_id: int,
        **kwargs
    ) -> Tuple[Optional[Notebook], Optional[str]]:
        """
        Atualizar notebook
        
        Campos atualizáveis:
        - title
        - description
        - is_public
        - is_archived
        - kernel_type
        
        Args:
            notebook_id: ID do notebook
            user_id: ID do usuário (validação)
            **kwargs: Campos a atualizar
        
        Returns:
            (Notebook, None) ou (None, mensagem_erro)
        """
        
        try:
            notebook = Notebook.query.get(notebook_id)
            
            if not notebook:
                return None, "Notebook não encontrado"
            
            # Autorização
            if notebook.user_id != user_id:
                return None, "Sem permissão"
            
            # Campos permitidos
            allowed_fields = {
                'title', 'description', 'is_public',
                'is_archived', 'kernel_type'
            }
            
            for field, value in kwargs.items():
                if field not in allowed_fields:
                    continue
                
                # Validar title
                if field == 'title':
                    if not value or len(value.strip()) == 0:
                        return None, "Título é obrigatório"
                    if len(value) > 255:
                        return None, "Título muito longo"
                    value = value.strip()
                
                # Validar description
                if field == 'description' and value:
                    value = value.strip()
                
                setattr(notebook, field, value)
            
            notebook.updated_at = datetime.utcnow()
            db.session.commit()
            
            return notebook, None
        
        except Exception as e:
            db.session.rollback()
            return None, f"Erro ao atualizar: {str(e)}"
    
    @staticmethod
    def delete_notebook(
        notebook_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Deletar notebook (soft delete com opção hard)
        
        Args:
            notebook_id: ID do notebook
            user_id: ID do usuário (validação)
        
        Returns:
            (sucesso, mensagem_erro)
        """
        
        try:
            notebook = Notebook.query.get(notebook_id)
            
            if not notebook:
                return False, "Notebook não encontrado"
            
            # Autorização
            if notebook.user_id != user_id:
                return False, "Sem permissão"
            
            # Hard delete (cascata deleta cells, executions, etc)
            db.session.delete(notebook)
            db.session.commit()
            
            return True, None
        
        except Exception as e:
            db.session.rollback()
            return False, f"Erro ao deletar: {str(e)}"
    
    @staticmethod
    def get_notebook_stats(notebook_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obter estatísticas do notebook
        
        Args:
            notebook_id: ID do notebook
            user_id: ID do usuário (validação)
        
        Returns:
            Dict com stats ou None
        """
        
        notebook = NotebookService.get_notebook(notebook_id, user_id)
        
        if not notebook:
            return None
        
        # Contar células
        cell_count = Cell.query.filter_by(notebook_id=notebook_id).count()
        code_count = Cell.query.filter_by(
            notebook_id=notebook_id,
            cell_type='code'
        ).count()
        markdown_count = Cell.query.filter_by(
            notebook_id=notebook_id,
            cell_type='markdown'
        ).count()
        
        # Total execuções
        from app.models.execution import Execution
        execution_count = db.session.query(Execution).join(Cell).filter(
            Cell.notebook_id == notebook_id
        ).count()
        
        return {
            'notebook_id': notebook_id,
            'cell_count': cell_count,
            'code_cells': code_count,
            'markdown_cells': markdown_count,
            'total_executions': execution_count,
            'created_at': notebook.created_at.isoformat(),
            'updated_at': notebook.updated_at.isoformat(),
        }
