"""
Executor Service - Executa código Python de forma isolada com timeout.
Versão para Pydroid: trata referências circulares e cria pasta tmp segura.
"""

import os
import sys
import json
import time
import tempfile
import subprocess
import traceback
import re
import logging
import textwrap
from typing import Dict, Any, Tuple
from . import kernel_manager

logging.basicConfig(level=logging.INFO, format='[ExecutorService] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

_TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
os.makedirs(_TEMP_DIR, exist_ok=True)
tempfile.tempdir = _TEMP_DIR

def _sanitize_code(code: str) -> str:
    lines = code.splitlines()
    sanitized = []
    for line in lines:
        if re.match(r'^\s*(exit|quit)\s*\(', line):
            line = f"# {line}  # desativado"
        sanitized.append(line)
    return "\n".join(sanitized)

def _safe_json_dumps(obj, max_depth=5) -> str:
    """Serializa para JSON ignorando referências circulares e objetos complexos."""
    seen = set()
    def _serialize(o, depth=0):
        if depth > max_depth:
            return "<max_depth_exceeded>"
        if id(o) in seen:
            return "<circular_reference>"
        if isinstance(o, (str, int, float, bool, type(None))):
            return o
        if isinstance(o, (list, tuple)):
            seen.add(id(o))
            result = [_serialize(item, depth+1) for item in o]
            seen.remove(id(o))
            return result
        if isinstance(o, dict):
            seen.add(id(o))
            result = {str(k): _serialize(v, depth+1) for k, v in o.items()}
            seen.remove(id(o))
            return result
        return f"<non_serializable: {type(o).__name__}>"
    try:
        return json.dumps(_serialize(obj))
    except Exception:
        return '{"error": "failed to serialize"}'

def execute_code(code: str, notebook_id: int, timeout_sec: int = 30) -> Tuple[bool, Dict]:
    code = _sanitize_code(code)

    # Obtém o estado atual da sessão (variáveis do notebook)
    session = kernel_manager.get_session(notebook_id)
    # Filtra apenas variáveis serializáveis (ignora __builtins__, etc.)
    serializable_globals = {}
    for key, value in session.items():
        if key.startswith('__') or key in ('__builtins__', '__name__', '__doc__', '__package__', '__loader__', '__spec__'):
            continue
        try:
            # Testa se é serializável
            _safe_json_dumps(value)
            serializable_globals[key] = value
        except Exception:
            logger.debug(f"Variável '{key}' não serializável, ignorando")
            pass

    # Converte o estado para string JSON segura
    serialized_globals_str = _safe_json_dumps(serializable_globals)

    # Prepara o código do usuário indentado
    indented_code = textwrap.indent(code, '        ')
    if not indented_code.strip():
        indented_code = '        pass'

    # Template do script (sem f-string para evitar conflitos)
    script_template = '''import sys
import json
import time
import traceback
from io import StringIO

# Guarda referências originais (protege contra sobrescrita pelo usuário)
_orig_stdout = sys.stdout
_orig_stderr = sys.stderr
_StringIO = StringIO
_json_loads = json.loads
_json_dumps = json.dumps
_traceback_print_exc = traceback.print_exc

# Restaura as variáveis da sessão
_user_globals = _json_loads(''' + repr(serialized_globals_str) + ''')
# Insere no namespace global (sem sobrescrever nomes críticos)
for k, v in _user_globals.items():
    # Se o nome colidir com uma função essencial, guarda com prefixo __user_
    if k in ('sys', 'json', 'time', 'traceback', 'StringIO', '_orig_stdout', '_orig_stderr', '_StringIO', '_json_loads', '_json_dumps', '_traceback_print_exc', '_user_globals'):
        globals()['__user_' + k] = v
    else:
        globals()[k] = v

# Redireciona stdout/stderr
stdout_cap = _StringIO()
stderr_cap = _StringIO()
sys.stdout = stdout_cap
sys.stderr = stderr_cap

start = time.time()
success = True
error_msg = None
logs = ""
try:
__INDENTED_CODE__
except Exception as e:
    success = False
    error_msg = str(e)
    _traceback_print_exc()
end = time.time()

logs = stdout_cap.getvalue()
stderr = stderr_cap.getvalue()
if stderr:
    logs += "\\n[stderr]\\n" + stderr

# Coleta novas variáveis definidas pelo usuário (exceto as internas)
new_globals = {}
for k, v in list(globals().items()):
    # Ignora variáveis internas, funções especiais e as que já existiam
    if k.startswith('_') or k in ('stdout_cap', 'stderr_cap', 'start', 'end', 'success', 'error_msg', 'logs', 'new_globals'):
        continue
    if k in _user_globals or ('__user_' + k) in _user_globals:
        continue
    # Remove prefixo __user_ se existir (caso colidido)
    if k.startswith('__user_'):
        k = k[7:]
    try:
        _json_dumps(v)  # teste rápido
        new_globals[k] = v
    except:
        pass

# Reinsere variáveis que foram colididas (sem o prefixo)
for k, v in list(globals().items()):
    if k.startswith('__user_') and k not in _user_globals:
        new_globals[k[7:]] = v

result = {
    "success": success,
    "logs": logs,
    "execution_time": end - start,
    "error_message": error_msg,
    "new_globals": new_globals
}

sys.stdout = _orig_stdout
sys.stderr = _orig_stderr

def _safe_json_dumps(obj, max_depth=5):
    seen = set()
    def _serialize(o, depth=0):
        if depth > max_depth:
            return "<max_depth_exceeded>"
        if id(o) in seen:
            return "<circular_reference>"
        if isinstance(o, (str, int, float, bool, type(None))):
            return o
        if isinstance(o, (list, tuple)):
            seen.add(id(o))
            result = [_serialize(item, depth+1) for item in o]
            seen.remove(id(o))
            return result
        if isinstance(o, dict):
            seen.add(id(o))
            result = {str(k): _serialize(v, depth+1) for k, v in o.items()}
            seen.remove(id(o))
            return result
        return f"<non_serializable: {type(o).__name__}>"
    try:
        return _json_dumps(_serialize(obj))
    except:
        return '{"error": "failed to serialize"}'

print("__RESULT__" + _safe_json_dumps(result))
'''

    script_content = script_template.replace('__INDENTED_CODE__', indented_code)

    # Cria arquivo temporário
    fd = None
    temp_path = None
    try:
        fd, temp_path = tempfile.mkstemp(suffix='.py', dir=_TEMP_DIR, text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(script_content)
        logger.info(f"Script temporário: {temp_path}")
    except Exception as e:
        logger.error(f"Erro ao criar arquivo: {e}")
        if fd:
            os.close(fd)
        return False, {
            "logs": f"Erro interno: {e}",
            "execution_time": 0,
            "error_message": str(e)
        }

    try:
        start_time = time.time()
        proc = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=os.getcwd()
        )
        elapsed = time.time() - start_time

        output = proc.stdout
        stderr_output = proc.stderr

        if '__RESULT__' in output:
            result_json = output.split('__RESULT__')[-1].strip()
            try:
                result = json.loads(result_json)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return False, {
                    "logs": f"Erro ao decodificar JSON: {e}\nTrecho: {result_json[:200]}",
                    "execution_time": elapsed,
                    "error_message": "JSON decode error"
                }
        else:
            logger.warning("Marcador __RESULT__ não encontrado")
            return False, {
                "logs": f"STDOUT: {output}\nSTDERR: {stderr_output}",
                "execution_time": elapsed,
                "error_message": "Marcador __RESULT__ não encontrado"
            }

        if result.get("success"):
            # Atualiza a sessão com as novas variáveis
            kernel_manager.update_session(notebook_id, result.get("new_globals", {}))
            logger.info(f"Notebook {notebook_id} executado com sucesso em {result.get('execution_time', elapsed):.3f}s")
            return True, {
                "logs": result.get("logs", ""),
                "execution_time": result.get("execution_time", elapsed),
                "error_message": None
            }
        else:
            logger.warning(f"Notebook {notebook_id} falhou: {result.get('error_message')}")
            return False, {
                "logs": result.get("logs", ""),
                "execution_time": result.get("execution_time", elapsed),
                "error_message": result.get("error_message", "Erro desconhecido")
            }

    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except:
            pass
        return False, {
            "logs": f"Timeout após {timeout_sec}s",
            "execution_time": timeout_sec,
            "error_message": f"Timeout after {timeout_sec}s"
        }
    except Exception as e:
        logger.exception("Exceção no executor")
        return False, {
            "logs": traceback.format_exc(),
            "execution_time": 0,
            "error_message": str(e)
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Não foi possível remover {temp_path}: {e}")