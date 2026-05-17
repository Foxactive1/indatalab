from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.services.dataset_service import save_dataset, load_dataset_data
from app.models.dataset import Dataset
from app.models.notebook import Notebook
from app.database.db import db
from app.executor.kernel_manager import refresh_datasets_in_session
import os
import json

bp = Blueprint('datasets', __name__, url_prefix='/api/notebooks/<int:notebook_id>/datasets')

def get_user_id():
    # 🔧 Temporário: usuário padrão (primeiro ativo)
    from app.models.user import User
    user = User.query.filter_by(is_active=True).first()
    if not user:
        user = User(name="Default", email="default@example.com", password_hash="", is_active=True)
        db.session.add(user)
        db.session.commit()
    return user.id

@bp.route('', methods=['POST'])
def upload_dataset(notebook_id):
    user_id = get_user_id()
    notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
    if not notebook:
        return jsonify({'success': False, 'error': 'Notebook não encontrado'}), 404
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Arquivo vazio'}), 400
    
    try:
        dataset = save_dataset(file, notebook_id, user_id)
        # 🔁 Sincroniza o kernel para que _datasets seja atualizado
        refresh_datasets_in_session(notebook_id)
        return jsonify({'success': True, 'dataset': dataset.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('', methods=['GET'])
def list_datasets(notebook_id):
    user_id = get_user_id()
    datasets = Dataset.query.filter_by(notebook_id=notebook_id).all()
    return jsonify({'success': True, 'datasets': [d.to_dict() for d in datasets]})

@bp.route('/<int:dataset_id>/data', methods=['GET'])
def get_dataset_data(notebook_id, dataset_id):
    user_id = get_user_id()
    try:
        data = load_dataset_data(dataset_id, user_id, notebook_id)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@bp.route('/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(notebook_id, dataset_id):
    user_id = get_user_id()
    dataset = Dataset.query.filter_by(id=dataset_id, notebook_id=notebook_id).first()
    if not dataset:
        return jsonify({'success': False, 'error': 'Dataset não encontrado'}), 404
    
    # Remove arquivo físico
    if os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)
    
    db.session.delete(dataset)
    db.session.commit()
    # 🔁 Sincroniza o kernel (remove o dataset de _datasets)
    refresh_datasets_in_session(notebook_id)
    return jsonify({'success': True})