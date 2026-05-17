"""
Kernel Manager - Gerencia o estado (variáveis) de cada notebook.
Cada notebook tem seu próprio namespace de execução.
Injeta automaticamente o dicionário _datasets com os arquivos enviados.
"""

import time
import threading
import json
import builtins
from typing import Dict, Any

# Armazenamento em memória
_sessions: Dict[int, Dict[str, Any]] = {}      # notebook_id -> globals
_last_activity: Dict[int, float] = {}          # último acesso
_SESSION_TIMEOUT = 1800  # 30 minutos sem atividade -> limpar

def _cleanup_expired():
    """Remove sessões inativas periodicamente."""
    now = time.time()
    expired = [nid for nid, last in _last_activity.items() if now - last > _SESSION_TIMEOUT]
    for nid in expired:
        _sessions.pop(nid, None)
        _last_activity.pop(nid, None)

def _start_cleanup_thread():
    """Thread de limpeza a cada 5 minutos."""
    def cleaner():
        while True:
            time.sleep(300)
            _cleanup_expired()
    threading.Thread(target=cleaner, daemon=True).start()

_start_cleanup_thread()

def _load_datasets_into_session(notebook_id: int, session_dict: Dict[str, Any]):
    """
    Consulta o banco e insere o dicionário _datasets na sessão.
    Cada entrada contém: id, filename, path, file_type, rows, columns, column_names, size_bytes.
    """
    try:
        from app.database.db import db
        from app.models.dataset import Dataset
        datasets = db.session.query(Dataset).filter_by(notebook_id=notebook_id).all()
        datasets_info = {}
        for ds in datasets:
            col_names = []
            if ds.column_names:
                try:
                    col_names = json.loads(ds.column_names)
                except Exception:
                    col_names = []
            datasets_info[ds.filename] = {
                "id": ds.id,
                "filename": ds.filename,
                "path": ds.file_path,
                "file_type": ds.file_type,
                "rows": ds.rows,
                "columns": ds.columns,
                "column_names": col_names,
                "size_bytes": ds.file_size,
            }
        session_dict["_datasets"] = datasets_info
    except Exception as e:
        print(f"[KernelManager] Erro ao carregar datasets para notebook {notebook_id}: {e}")
        session_dict["_datasets"] = {}

def get_session(notebook_id: int) -> Dict[str, Any]:
    """Retorna o namespace do notebook (cria se não existir)."""
    _last_activity[notebook_id] = time.time()
    if notebook_id not in _sessions:
        # Cria namespace seguro
        safe_builtins = dict(vars(builtins))
        for dangerous in ['open', 'eval', 'exec', 'compile', 'breakpoint', 'input']:
            safe_builtins.pop(dangerous, None)
        _sessions[notebook_id] = {
            '__builtins__': safe_builtins,
            '__name__': f'notebook_{notebook_id}',
        }
        # Injeta datasets na sessão
        _load_datasets_into_session(notebook_id, _sessions[notebook_id])
    return _sessions[notebook_id]

def update_session(notebook_id: int, new_globals: Dict[str, Any]):
    """Atualiza o namespace com novos símbolos (ignora __*)."""
    session = get_session(notebook_id)
    for key, value in new_globals.items():
        if not key.startswith('__'):
            session[key] = value
    _last_activity[notebook_id] = time.time()

def refresh_datasets_in_session(notebook_id: int):
    """Atualiza a variável _datasets na sessão existente (após upload/delete)."""
    if notebook_id in _sessions:
        _load_datasets_into_session(notebook_id, _sessions[notebook_id])
        _last_activity[notebook_id] = time.time()

def delete_session(notebook_id: int):
    """Remove sessão quando notebook for deletado."""
    _sessions.pop(notebook_id, None)
    _last_activity.pop(notebook_id, None)