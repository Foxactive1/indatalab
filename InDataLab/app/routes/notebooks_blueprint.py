"""
Blueprint: Notebooks
Rotas CRUD para notebooks
"""

from flask import Blueprint, request, jsonify

from app.services.notebook_service import NotebookService
from app.utils import APIResponse, ValidateRequest, serialize_model, serialize_models


notebooks_bp = Blueprint(
    'notebooks',
    __name__,
    url_prefix='/api/notebooks'
)


# CRIAR NOTEBOOK
@notebooks_bp.route('', methods=['POST'])
def create_notebook():
    """
    POST /api/notebooks
    
    Body:
    {
        "title": "Meu Notebook",
        "description": "Opcional",
        "is_public": false,
        "kernel_type": "python3"
    }
    """
    
    try:
        data = request.get_json() or {}
        
        # Validação
        validation_error = ValidateRequest.required_fields(data, ['title'])
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]
        
        validation_error = ValidateRequest.field_length(
            data, 'title', min_length=1, max_length=255
        )
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]
        
        # Hardcoded para MVP (autenticação viria depois)
        user_id = 1
        
        # Criar
        notebook, error = NotebookService.create_notebook(
            user_id=user_id,
            title=data.get('title'),
            description=data.get('description'),
            is_public=data.get('is_public', False),
            kernel_type=data.get('kernel_type', 'python3')
        )
        
        if error:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(
            data=serialize_model(notebook),
            message="Notebook criado com sucesso",
            status_code=201
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# LISTAR NOTEBOOKS (paginado)
@notebooks_bp.route('', methods=['GET'])
def list_notebooks():
    """
    GET /api/notebooks?page=1&per_page=20&is_archived=false
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        is_archived = request.args.get('is_archived', type=lambda x: x.lower() == 'true')
        
        # Validar pagination
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        notebooks, total, pages = NotebookService.list_notebooks(
            user_id=user_id,
            is_archived=is_archived,
            page=page,
            per_page=per_page
        )
        
        resp, code = APIResponse.success(
            data={
                'notebooks': serialize_models(notebooks),
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': pages
                }
            }
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# OBTER NOTEBOOK (com stats)
@notebooks_bp.route('/<int:notebook_id>', methods=['GET'])
def get_notebook(notebook_id):
    """
    GET /api/notebooks/{notebook_id}
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        notebook = NotebookService.get_notebook(notebook_id, user_id)
        
        if not notebook:
            resp, code = APIResponse.not_found("Notebook")
            return jsonify(resp), code
        
        # Buscar stats
        stats = NotebookService.get_notebook_stats(notebook_id, user_id)
        
        resp, code = APIResponse.success(
            data={
                'notebook': serialize_model(notebook),
                'stats': stats
            }
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# ATUALIZAR NOTEBOOK
@notebooks_bp.route('/<int:notebook_id>', methods=['PUT'])
def update_notebook(notebook_id):
    """
    PUT /api/notebooks/{notebook_id}
    
    Body: Qualquer combinação de campos atualizáveis
    {
        "title": "Novo título",
        "description": "Nova descrição",
        "is_public": true,
        "is_archived": false
    }
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        data = request.get_json() or {}
        
        if not data:
            resp, code = APIResponse.bad_request("Nenhum dado para atualizar")
            return jsonify(resp), code
        
        # Atualizar
        notebook, error = NotebookService.update_notebook(
            notebook_id=notebook_id,
            user_id=user_id,
            **data
        )
        
        if error:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(
            data=serialize_model(notebook),
            message="Notebook atualizado"
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# DELETAR NOTEBOOK
@notebooks_bp.route('/<int:notebook_id>', methods=['DELETE'])
def delete_notebook(notebook_id):
    """
    DELETE /api/notebooks/{notebook_id}
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        success, error = NotebookService.delete_notebook(notebook_id, user_id)
        
        if not success:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(
            message="Notebook deletado"
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code
