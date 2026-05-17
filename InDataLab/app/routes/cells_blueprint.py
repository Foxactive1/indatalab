"""
Blueprint: Cells
Rotas CRUD para células dentro de notebooks
"""

from flask import Blueprint, request, jsonify

from app.services.cell_service import CellService
from app.utils import APIResponse, ValidateRequest, serialize_model, serialize_models


cells_bp = Blueprint(
    'cells',
    __name__,
    url_prefix='/api/notebooks/<int:notebook_id>/cells'
)


# CRIAR CÉLULA
@cells_bp.route('', methods=['POST'])
def create_cell(notebook_id):
    """
    POST /api/notebooks/{notebook_id}/cells
    
    Body:
    {
        "cell_type": "code",  # ou "markdown"
        "content": "print('hello')",
        "position": null,  # opcional, vai para fim se null
        "tags": "análise,teste"  # opcional
    }
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        data = request.get_json() or {}
        
        # Validação
        validation_error = ValidateRequest.required_fields(
            data, ['cell_type', 'content']
        )
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]
        
        # Criar
        cell, error = CellService.create_cell(
            notebook_id=notebook_id,
            user_id=user_id,
            cell_type=data.get('cell_type'),
            content=data.get('content'),
            position=data.get('position'),
            tags=data.get('tags')
        )
        
        if error:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(
            data=serialize_model(cell),
            message="Célula criada",
            status_code=201
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# LISTAR CÉLULAS (ordenadas por position)
@cells_bp.route('', methods=['GET'])
def list_cells(notebook_id):
    """
    GET /api/notebooks/{notebook_id}/cells?cell_type=code
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        cell_type = request.args.get('cell_type')  # opcional
        
        cells, error = CellService.list_cells(
            notebook_id=notebook_id,
            user_id=user_id,
            cell_type=cell_type
        )
        
        if error:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(
            data={'cells': serialize_models(cells)}
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# OBTER CÉLULA
@cells_bp.route('/<int:cell_id>', methods=['GET'])
def get_cell(notebook_id, cell_id):
    """
    GET /api/notebooks/{notebook_id}/cells/{cell_id}
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        cell = CellService.get_cell(cell_id, user_id)
        
        # Validar que célula pertence ao notebook
        if not cell or cell.notebook_id != notebook_id:
            resp, code = APIResponse.not_found("Célula")
            return jsonify(resp), code
        
        resp, code = APIResponse.success(
            data=serialize_model(cell)
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# ATUALIZAR CÉLULA
@cells_bp.route('/<int:cell_id>', methods=['PUT'])
def update_cell(notebook_id, cell_id):
    """
    PUT /api/notebooks/{notebook_id}/cells/{cell_id}
    
    Body:
    {
        "content": "novo código",
        "cell_type": "code",
        "output": "resultado da execução",
        "position": 2,
        "is_hidden": false,
        "tags": "novo,tags"
    }
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        cell = CellService.get_cell(cell_id, user_id)
        
        if not cell or cell.notebook_id != notebook_id:
            resp, code = APIResponse.not_found("Célula")
            return jsonify(resp), code
        
        data = request.get_json() or {}
        
        if not data:
            resp, code = APIResponse.bad_request("Nenhum dado para atualizar")
            return jsonify(resp), code
        
        # Atualizar
        cell_updated, error = CellService.update_cell(
            cell_id=cell_id,
            user_id=user_id,
            **data
        )
        
        if error:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(
            data=serialize_model(cell_updated),
            message="Célula atualizada"
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# DELETAR CÉLULA
@cells_bp.route('/<int:cell_id>', methods=['DELETE'])
def delete_cell(notebook_id, cell_id):
    """
    DELETE /api/notebooks/{notebook_id}/cells/{cell_id}
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        cell = CellService.get_cell(cell_id, user_id)
        
        if not cell or cell.notebook_id != notebook_id:
            resp, code = APIResponse.not_found("Célula")
            return jsonify(resp), code
        
        success, error = CellService.delete_cell(cell_id, user_id)
        
        if not success:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(
            message="Célula deletada"
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# REORDENAR CÉLULAS
@cells_bp.route('/reorder', methods=['POST'])
def reorder_cells(notebook_id):
    """
    POST /api/notebooks/{notebook_id}/cells/reorder
    
    Body:
    {
        "cell_order": [cell_id_1, cell_id_2, cell_id_3, ...]
    }
    """
    
    try:
        user_id = 1  # Hardcoded para MVP
        
        data = request.get_json() or {}
        
        # Validação
        validation_error = ValidateRequest.required_fields(data, ['cell_order'])
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]
        
        cell_order = data.get('cell_order')
        
        if not isinstance(cell_order, list):
            resp, code = APIResponse.bad_request("cell_order deve ser uma lista")
            return jsonify(resp), code
        
        # Reordenar
        success, error = CellService.reorder_cells(
            notebook_id=notebook_id,
            user_id=user_id,
            cell_order=cell_order
        )
        
        if not success:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(
            message="Células reordenadas"
        )
        return jsonify(resp), code
    
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code
