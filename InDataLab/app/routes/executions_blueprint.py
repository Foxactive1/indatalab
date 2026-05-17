"""
Blueprint: Executions
Rotas para rastreamento e histórico de execuções de células
"""

from flask import Blueprint, request, jsonify

from app.services.execution_service import ExecutionService
from app.services.cell_service import CellService
from app.executor.executor_service import execute_code
from app.database.db import db
from app.utils import APIResponse, ValidateRequest, serialize_model, serialize_models


executions_bp = Blueprint(
    'executions',
    __name__,
    url_prefix='/api/notebooks'
)


# EXECUTAR CÉLULA (cria execução e roda código real)
@executions_bp.route('/<int:notebook_id>/cells/<int:cell_id>/execute', methods=['POST'])
def create_execution(notebook_id, cell_id):
    """
    POST /api/notebooks/{notebook_id}/cells/{cell_id}/execute
    Executa o código da célula e retorna o resultado.
    """
    try:
        user_id = 1  # Hardcoded MVP

        from app.models.cell import Cell
        from app.models.notebook import Notebook

        cell = Cell.query.filter_by(id=cell_id, notebook_id=notebook_id).first()
        if not cell:
            resp, code = APIResponse.not_found("Célula")
            return jsonify(resp), code

        notebook = Notebook.query.get(notebook_id)
        if not notebook or notebook.user_id != user_id:
            resp, code = APIResponse.not_found("Notebook")
            return jsonify(resp), code

        if cell.cell_type != 'code':
            resp, code = APIResponse.bad_request("Apenas células de código podem ser executadas")
            return jsonify(resp), code

        # Criar registro de execução (status running)
        execution, error = ExecutionService.create_execution(
            cell_id=cell_id,
            status='running'
        )
        if error:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code

        # Executar código real
        success, result = execute_code(
            code=cell.content,
            notebook_id=notebook_id,
            timeout_sec=30          # <-- atenção ao nome
        )

        # Atualizar execução com resultado
        if success:
            execution.status = 'success'
            execution.logs = result['logs']
            execution.execution_time = result['execution_time']
            execution.error_message = None
        else:
            execution.status = 'error'
            execution.logs = result['logs']
            execution.execution_time = result['execution_time']
            execution.error_message = result['error_message']

        db.session.commit()

        # Incrementar contador da célula
        CellService.increment_execution_count(cell_id)

        # Salvar última saída na célula
        cell.output = result['logs'][:500] if result['logs'] else ''
        db.session.commit()

        resp, code = APIResponse.success(
            data=serialize_model(execution),
            message="Código executado com sucesso" if success else "Falha na execução"
        )
        return jsonify(resp), code

    except Exception as e:
        db.session.rollback()
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# OBTER EXECUÇÃO
@executions_bp.route('/<int:notebook_id>/executions/<int:execution_id>', methods=['GET'])
def get_execution(notebook_id, execution_id):
    try:
        user_id = 1
        execution = ExecutionService.get_execution(execution_id, user_id)
        if not execution:
            resp, code = APIResponse.not_found("Execução")
            return jsonify(resp), code
        resp, code = APIResponse.success(data=serialize_model(execution))
        return jsonify(resp), code
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# ATUALIZAR EXECUÇÃO (caso precise manualmente)
@executions_bp.route('/<int:notebook_id>/executions/<int:execution_id>', methods=['PUT'])
def update_execution(notebook_id, execution_id):
    try:
        user_id = 1
        data = request.get_json() or {}
        if not data:
            resp, code = APIResponse.bad_request("Nenhum dado para atualizar")
            return jsonify(resp), code
        
        execution, error = ExecutionService.update_execution(
            execution_id=execution_id,
            user_id=user_id,
            **data
        )
        if error:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        CellService.increment_execution_count(execution.cell_id)
        
        resp, code = APIResponse.success(
            data=serialize_model(execution),
            message="Execução atualizada"
        )
        return jsonify(resp), code
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# LISTAR EXECUÇÕES DE UMA CÉLULA
@executions_bp.route('/<int:notebook_id>/cells/<int:cell_id>/executions', methods=['GET'])
def list_cell_executions(notebook_id, cell_id):
    try:
        user_id = 1
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        if page < 1: page = 1
        if limit < 1 or limit > 100: limit = 50
        
        executions, error = ExecutionService.list_cell_executions(
            cell_id=cell_id, user_id=user_id, limit=limit, page=page
        )
        if error:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(data={
            'executions': serialize_models(executions),
            'pagination': {'page': page, 'limit': limit}
        })
        return jsonify(resp), code
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# LISTAR TODAS EXECUÇÕES DO NOTEBOOK
@executions_bp.route('/<int:notebook_id>/executions', methods=['GET'])
def list_notebook_executions(notebook_id):
    try:
        user_id = 1
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        if page < 1: page = 1
        if limit < 1 or limit > 200: limit = 100
        
        executions, total, pages, error = ExecutionService.list_notebook_executions(
            notebook_id=notebook_id, user_id=user_id, limit=limit, page=page
        )
        if error:
            resp, code = APIResponse.bad_request(error)
            return jsonify(resp), code
        
        resp, code = APIResponse.success(data={
            'executions': serialize_models(executions),
            'pagination': {'page': page, 'limit': limit, 'total': total, 'pages': pages}
        })
        return jsonify(resp), code
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code


# STATS DE EXECUÇÃO DE UMA CÉLULA
@executions_bp.route('/<int:notebook_id>/cells/<int:cell_id>/stats', methods=['GET'])
def get_cell_execution_stats(notebook_id, cell_id):
    try:
        user_id = 1
        stats = ExecutionService.get_execution_stats(cell_id, user_id)
        if stats is None:
            resp, code = APIResponse.not_found("Célula")
            return jsonify(resp), code
        resp, code = APIResponse.success(data=stats)
        return jsonify(resp), code
    except Exception as e:
        resp, code = APIResponse.internal_error(str(e))
        return jsonify(resp), code