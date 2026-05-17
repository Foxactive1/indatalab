from flask import Blueprint, request, jsonify, g
from app.services.ai_service import AIService
from app.services.notebook_service import NotebookService
from app.database.db import db
from app.models.notebook import Notebook
from app.models.cell import Cell
import logging

bp = Blueprint('copilot', __name__, url_prefix='/api/copilot')
logger = logging.getLogger(__name__)

def get_notebook_context(notebook_id: int, user_id: int) -> str:
    """Coleta todo o conteúdo relevante do notebook para o contexto da IA."""
    notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
    if not notebook:
        return "Notebook não encontrado."
    
    cells = Cell.query.filter_by(notebook_id=notebook_id).order_by(Cell.position.asc()).all()
    
    context = f"# Notebook: {notebook.title}\n"
    if notebook.description:
        context += f"Descrição: {notebook.description}\n"
    context += f"Kernel: {notebook.kernel_type}\n\n"
    context += "## Células (na ordem atual):\n"
    
    for idx, cell in enumerate(cells, 1):
        context += f"\n### Célula {idx} - Tipo: {cell.cell_type}\n"
        context += f"Conteúdo:\n```{cell.cell_type}\n{cell.content}\n```\n"
        if cell.output and cell.cell_type == 'code':
            # Mostra apenas as últimas 500 chars da saída para não estourar tokens
            output_preview = cell.output[:1000] + ('…' if len(cell.output) > 1000 else '')
            context += f"Última saída:\n```\n{output_preview}\n```\n"
    
    return context

@bp.route('/notebooks/<int:notebook_id>/chat', methods=['POST'])
def copilot_chat(notebook_id):
    user_id = g.user.id  # Assumindo que você tem autenticação e g.user
    data = request.get_json()
    user_message = data.get('message', '').strip()
    conversation_session_id = data.get('session_id')  # opcional, para manter histórico
    
    if not user_message:
        return jsonify({'success': False, 'error': 'Mensagem vazia'}), 400
    
    # Obtém contexto completo do notebook
    context = get_notebook_context(notebook_id, user_id)
    
    # System prompt instruindo o modelo a ser um copilot para notebooks
    system_prompt = f"""
Você é um assistente de IA especializado em notebooks interativos (como Jupyter/InDataLab). 
Você tem acesso ao seguinte notebook atual:

{context}

Seu papel é:
1. Responder perguntas sobre o código, dados e saídas presentes no notebook.
2. Sugerir melhorias, correções ou novas células de código (Python) ou markdown.
3. Quando sugerir código, forneça-o em um bloco markdown com a linguagem especificada (python ou markdown).
4. Seja conciso, direto e útil. Não invente dados que não estão no contexto.
5. Se o usuário pedir para criar uma nova célula, indique o código sugerido e explique onde inseri-la.
6. Nunca execute código no sistema real; apenas dê instruções.
"""
    
    # Inicializa o AIService
    ai = AIService()
    result = ai.chat_completion(
        user_id=user_id,
        content=user_message,
        notebook_id=notebook_id,
        conversation_session_id=conversation_session_id,
        system_prompt=system_prompt,
        temperature=0.5,          # um pouco mais conservador para código
        model='llama-3.3-70b-versatile'
    )
    
    if result['success']:
        return jsonify({
            'success': True,
            'response': result['content'],
            'message_id': result['message_id'],
            'tokens': result['tokens']
        })
    else:
        return jsonify({'success': False, 'error': result['error']}), 500