import os
import csv
import json
from werkzeug.utils import secure_filename
from flask import current_app
from app.database.db import db
from app.models.dataset import Dataset

ALLOWED_EXTENSIONS = {'csv', 'txt','json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_dataset(file, notebook_id, user_id):
    """Salva arquivo, lê metadados e registra no banco"""
    if not allowed_file(file.filename):
        raise ValueError("Apenas arquivos .csv ou .txt são permitidos")
    
    original_name = secure_filename(file.filename)
    base, ext = os.path.splitext(original_name)
    display_name = base if base else "dataset"
    
    # Cria diretório do notebook dentro de uploads
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(notebook_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Caminho absoluto para salvar
    filepath = os.path.join(upload_dir, original_name)
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    
    # Lê metadados
    rows, cols, column_names = 0, 0, []
    if ext.lower() == '.csv':
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = list(reader)
            rows = len(data)
            if rows > 0:
                cols = len(data[0])
                column_names = data[0]  # primeira linha como cabeçalho
    else:  # txt
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            rows = len(lines)
            cols = max(len(line.split()) for line in lines) if lines else 0
    
    dataset = Dataset(
        notebook_id=notebook_id,
        filename=original_name,
        file_type=ext[1:],
        file_path=filepath,
        file_size=file_size,
        rows=rows,
        columns=cols,
        column_names=json.dumps(column_names) if column_names else None,
        description=f"Importado de {original_name}",
        is_public=False,
        extra_metadata=json.dumps({"user_id": user_id})
    )
    db.session.add(dataset)
    db.session.commit()
    return dataset

def load_dataset_data(dataset_id, user_id, notebook_id):
    """Carrega dados do dataset como lista de dicionários (CSV) ou lista de linhas (TXT)"""
    dataset = Dataset.query.filter_by(id=dataset_id, notebook_id=notebook_id).first()
    if not dataset:
        raise ValueError("Dataset não encontrado")
    
    # Verifica permissão (opcional: usuário dono do notebook)
    # Aqui você pode adicionar lógica de acesso
    
    if dataset.file_type == 'csv':
        with open(dataset.file_path, 'r', encoding='utf-8') as f:
            # Detecta se tem cabeçalho
            sample = f.read(1024)
            f.seek(0)
            has_header = csv.Sniffer().has_header(sample)
            reader = csv.DictReader(f) if has_header else csv.reader(f)
            if has_header:
                return list(reader)
            else:
                # Sem cabeçalho, retorna lista de listas
                return [row for row in reader]
    else:  # txt
        with open(dataset.file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]