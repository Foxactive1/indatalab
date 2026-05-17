"""
Service: AI (Groq)
Gerencia requisições para Groq API
Logging, tratamento de erros, rate limits
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from groq import Groq
except ImportError:
    Groq = None

from flask import current_app
from app.database.db import db
from app.models.ai_conversation import AIConversation


class AIService:
    """
    Serviço para integração com Groq API
    Gerencia conversas, chamadas de API, armazenamento
    """
    
    def __init__(self):
        """Inicializa cliente Groq - lê chave diretamente do ambiente"""
        if not Groq:
            raise ImportError(
                "groq not installed. Run: pip install groq"
            )
        
        # Tenta obter a chave de diferentes fontes
        api_key = None
        
        # 1. Tenta do Flask config
        try:
            api_key = current_app.config.get('GROQ_API_KEY')
        except RuntimeError:
            pass  # Fora do contexto da aplicação
        
        # 2. Se não, tenta variável de ambiente
        if not api_key:
            api_key = os.environ.get('GROQ_API_KEY')
        
        # 3. Se ainda não, tenta ler do arquivo .env manualmente
        if not api_key:
            try:
                from dotenv import load_dotenv
                load_dotenv()  # Tenta carregar de .env no diretório atual
                api_key = os.environ.get('GROQ_API_KEY')
            except ImportError:
                pass
        
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY não configurada. Defina a variável de ambiente ou crie um arquivo .env"
            )
        
        self.client = Groq(api_key=api_key)
        
        # Configurações (com fallback)
        self.model = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
        self.temperature = float(os.environ.get('GROQ_TEMPERATURE', 0.7))
        self.max_tokens = int(os.environ.get('GROQ_MAX_TOKENS', 2048))
        self.timeout = int(os.environ.get('GROQ_TIMEOUT', 30))
        
        # Se estiver no contexto Flask, sobrescreve com as configs da app
        try:
            self.model = current_app.config.get('GROQ_MODEL', self.model)
            self.temperature = current_app.config.get('GROQ_TEMPERATURE', self.temperature)
            self.max_tokens = current_app.config.get('GROQ_MAX_TOKENS', self.max_tokens)
            self.timeout = current_app.config.get('GROQ_TIMEOUT', self.timeout)
        except RuntimeError:
            pass
    
    def chat_completion(
        self,
        user_id: int,
        content: str,
        notebook_id: Optional[int] = None,
        cell_id: Optional[int] = None,
        conversation_session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Chamada de chat completion com Groq
        
        Args:
            user_id: ID do usuário
            content: Mensagem do usuário
            notebook_id: ID do notebook (contexto)
            cell_id: ID da célula (contexto)
            conversation_session_id: ID da sessão
            system_prompt: Prompt do sistema
            temperature: Temperatura (0-2)
            model: Modelo a usar
        
        Returns:
            Dict com resposta, tokens, etc
        """
        
        start_time = time.time()
        
        try:
            # Configurações
            temp = temperature or self.temperature
            m = model or self.model
            
            # Prepara mensagens
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Busca histórico da conversa (últimas 10 mensagens)
            history = self._get_conversation_history(conversation_session_id, limit=10)
            messages.extend(history)
            messages.append({"role": "user", "content": content})
            
            # Chamada Groq
            response = self.client.chat.completions.create(
                model=m,
                messages=messages,
                temperature=temp,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )
            
            # Processa resposta
            assistant_content = response.choices[0].message.content
            
            processing_time = (time.time() - start_time) * 1000  # ms
            
            # Tenta salvar no banco (se houver contexto)
            try:
                # Armazena mensagem do usuário
                user_msg = AIConversation(
                    user_id=user_id,
                    notebook_id=notebook_id,
                    cell_id=cell_id,
                    conversation_session_id=conversation_session_id,
                    role='user',
                    content=content,
                    model=m,
                    temperature=temp,
                )
                db.session.add(user_msg)
                
                # Armazena resposta da IA
                assistant_msg = AIConversation(
                    user_id=user_id,
                    notebook_id=notebook_id,
                    cell_id=cell_id,
                    conversation_session_id=conversation_session_id,
                    role='assistant',
                    content=assistant_content,
                    model=m,
                    temperature=temp,
                    tokens_used=response.usage.total_tokens,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    processing_time=processing_time,
                    groq_request_id=getattr(response, 'id', None),
                )
                db.session.add(assistant_msg)
                db.session.commit()
                message_id = assistant_msg.id
            except Exception as e:
                # Falha ao salvar no banco não impede a resposta
                print(f"Erro ao salvar conversa no banco: {e}")
                message_id = None
            
            return {
                'success': True,
                'content': assistant_content,
                'message_id': message_id,
                'tokens': {
                    'total': response.usage.total_tokens,
                    'prompt': response.usage.prompt_tokens,
                    'completion': response.usage.completion_tokens,
                },
                'processing_time_ms': processing_time,
                'model': m,
            }
        
        except Exception as e:
            print(f"Erro ao chamar Groq: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
            }
    
    def _get_conversation_history(
        self,
        session_id: Optional[str],
        limit: int = 10
    ) -> list:
        """
        Busca histórico da conversa
        
        Args:
            session_id: ID da sessão
            limit: Quantas mensagens retornar
        
        Returns:
            Lista de dicts com role e content
        """
        
        if not session_id:
            return []
        
        try:
            conversations = AIConversation.query.filter_by(
                conversation_session_id=session_id
            ).order_by(
                AIConversation.created_at.asc()
            ).limit(limit).all()
            
            return [
                {
                    "role": conv.role,
                    "content": conv.content
                }
                for conv in conversations
            ]
        except Exception:
            return []
    
    def get_conversation_history(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        notebook_id: Optional[int] = None,
        limit: int = 50
    ) -> list:
        """
        Busca histórico de conversas do usuário
        
        Args:
            user_id: ID do usuário
            session_id: ID da sessão (filtro)
            notebook_id: ID do notebook (filtro)
            limit: Limite de registros
        
        Returns:
            Lista de conversas serializadas
        """
        
        query = AIConversation.query.filter_by(user_id=user_id)
        
        if session_id:
            query = query.filter_by(conversation_session_id=session_id)
        
        if notebook_id:
            query = query.filter_by(notebook_id=notebook_id)
        
        conversations = query.order_by(
            AIConversation.created_at.desc()
        ).limit(limit).all()
        
        return [conv.to_dict() for conv in conversations]