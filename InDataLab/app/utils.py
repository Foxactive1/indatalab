"""
Utilities: Response, Error Handling
Respostas padrão JSON para toda a API
"""

from flask import jsonify
from typing import Any, Dict, Optional, Tuple


class APIResponse:
    """
    Resposta API padrão
    
    Sucesso:
    {
        "success": true,
        "data": {...},
        "message": "..."
    }
    
    Erro:
    {
        "success": false,
        "error": "...",
        "status_code": 400
    }
    """
    
    @staticmethod
    def success(
        data: Any = None,
        message: Optional[str] = None,
        status_code: int = 200
    ) -> Tuple[Dict, int]:
        """
        Resposta de sucesso
        
        Args:
            data: Dados a retornar (pode ser dict, list, objeto)
            message: Mensagem opcional
            status_code: Status HTTP
        
        Returns:
            (response_dict, status_code)
        """
        
        response = {
            "success": True,
            "data": data,
        }
        
        if message:
            response["message"] = message
        
        return response, status_code
    
    @staticmethod
    def error(
        error: str,
        status_code: int = 400,
        details: Optional[Dict] = None
    ) -> Tuple[Dict, int]:
        """
        Resposta de erro
        
        Args:
            error: Mensagem de erro
            status_code: Status HTTP
            details: Detalhes adicionais
        
        Returns:
            (response_dict, status_code)
        """
        
        response = {
            "success": False,
            "error": error,
            "status_code": status_code,
        }
        
        if details:
            response["details"] = details
        
        return response, status_code
    
    @staticmethod
    def not_found(resource: str = "Recurso") -> Tuple[Dict, int]:
        """404 padrão"""
        return APIResponse.error(
            f"{resource} não encontrado",
            status_code=404
        )
    
    @staticmethod
    def unauthorized() -> Tuple[Dict, int]:
        """401 padrão"""
        return APIResponse.error(
            "Não autorizado",
            status_code=401
        )
    
    @staticmethod
    def forbidden() -> Tuple[Dict, int]:
        """403 padrão"""
        return APIResponse.error(
            "Sem permissão",
            status_code=403
        )
    
    @staticmethod
    def bad_request(message: str) -> Tuple[Dict, int]:
        """400 padrão"""
        return APIResponse.error(
            message,
            status_code=400
        )
    
    @staticmethod
    def validation_error(errors: Dict[str, str]) -> Tuple[Dict, int]:
        """400 para erros de validação"""
        response = {
            "success": False,
            "error": "Erro de validação",
            "status_code": 400,
            "validation_errors": errors
        }
        return response, 400
    
    @staticmethod
    def internal_error(message: str = "Erro interno do servidor") -> Tuple[Dict, int]:
        """500 padrão"""
        return APIResponse.error(
            message,
            status_code=500
        )


class ValidateRequest:
    """
    Validação de requisições
    """
    
    @staticmethod
    def required_fields(data: Dict, fields: list) -> Optional[Tuple[Dict, int]]:
        """
        Validar campos obrigatórios
        
        Args:
            data: Request data (JSON)
            fields: Lista de campos obrigatórios
        
        Returns:
            (error_response, status) se falhar, None se OK
        """
        
        missing = []
        
        for field in fields:
            if field not in data or data[field] is None or data[field] == '':
                missing.append(field)
        
        if missing:
            response = {
                "success": False,
                "error": "Campos obrigatórios faltando",
                "status_code": 400,
                "missing_fields": missing
            }
            return response, 400
        
        return None
    
    @staticmethod
    def field_type(
        data: Dict,
        field: str,
        expected_type: type,
        allow_none: bool = False
    ) -> Optional[Tuple[Dict, int]]:
        """
        Validar tipo de campo
        
        Args:
            data: Request data
            field: Nome do campo
            expected_type: Tipo esperado (str, int, bool, etc)
            allow_none: Se None é permitido
        
        Returns:
            (error_response, status) se falhar, None se OK
        """
        
        if field not in data:
            return None
        
        value = data[field]
        
        if value is None and allow_none:
            return None
        
        if not isinstance(value, expected_type):
            response = {
                "success": False,
                "error": f"Campo '{field}' deve ser do tipo {expected_type.__name__}",
                "status_code": 400
            }
            return response, 400
        
        return None
    
    @staticmethod
    def field_length(
        data: Dict,
        field: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> Optional[Tuple[Dict, int]]:
        """
        Validar comprimento de string
        
        Args:
            data: Request data
            field: Nome do campo
            min_length: Comprimento mínimo
            max_length: Comprimento máximo
        
        Returns:
            (error_response, status) se falhar, None se OK
        """
        
        if field not in data:
            return None
        
        value = str(data[field])
        
        if min_length is not None and len(value) < min_length:
            response = {
                "success": False,
                "error": f"Campo '{field}' deve ter no mínimo {min_length} caracteres",
                "status_code": 400
            }
            return response, 400
        
        if max_length is not None and len(value) > max_length:
            response = {
                "success": False,
                "error": f"Campo '{field}' deve ter no máximo {max_length} caracteres",
                "status_code": 400
            }
            return response, 400
        
        return None


def serialize_model(model_obj: Any, exclude: list = None) -> Dict:
    """
    Serializar modelo para dict
    
    Args:
        model_obj: Instância de model
        exclude: Campos a excluir
    
    Returns:
        Dict serializável
    """
    
    if hasattr(model_obj, 'to_dict'):
        return model_obj.to_dict()
    
    # Fallback: converter manualmente
    result = {}
    for column in model_obj.__table__.columns:
        if exclude and column.name in exclude:
            continue
        
        value = getattr(model_obj, column.name)
        
        # Serializar datetime
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        
        result[column.name] = value
    
    return result


def serialize_models(models: list, exclude: list = None) -> list:
    """
    Serializar lista de modelos
    
    Args:
        models: Lista de instâncias
        exclude: Campos a excluir
    
    Returns:
        Lista de dicts
    """
    
    return [serialize_model(m, exclude) for m in models]
