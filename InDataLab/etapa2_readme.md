# 🚀 InDataLab - ETAPA 2: CRUD Consolidado

## ✅ Status

**ETAPA 1**: ✅ Fundação Backend + Models + Groq  
**ETAPA 2**: ✅ **CRUD Completo** (Blueprints + Services)  
**ETAPA 3**: ⏳ Notebook Engine + Python Executor  

---

## 📦 O que foi adicionado na ETAPA 2

### Services (Lógica de Negócio)
- ✅ `NotebookService` - CRUD notebooks
- ✅ `CellService` - CRUD células + reordenação
- ✅ `ExecutionService` - Histórico + stats

### Blueprints (Rotas)
- ✅ `/api/notebooks` - CRUD notebooks
- ✅ `/api/notebooks/{id}/cells` - CRUD células
- ✅ `/api/notebooks/{id}/executions` - Execuções + stats

### Utils
- ✅ `APIResponse` - Response padrão JSON
- ✅ `ValidateRequest` - Validação centralizada

### Testes
- ✅ `API_TEST.md` - Exemplos cURL
- ✅ `test_api.py` - Script de teste em Python
- ✅ `ETAPA_2.md` - Documentação completa

---

## 🏃 Quick Start (5 minutos)

### 1️⃣ Setup (primeira vez)

```bash
cd indatalab
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Inicializar banco (primeira vez)

```bash
export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 3️⃣ Configurar Groq (IMPORTANTE)

```bash
nano .env
# Adicionar: GROQ_API_KEY=sua_chave_aqui
```

### 4️⃣ Rodar servidor

```bash
python run.py
```

Esperado:
```
╔═══════════════════════════════════╗
║    InDataLab - ETAPA 1 - MVP      ║
║    Backend Consolidado            ║
╚═══════════════════════════════════╝

Flask: True
Database: sqlite:///instance/indatalab.db
Groq Model: llama-3.3-70b-versatile

▶ Servidor rodando em http://localhost:5000
```

### 5️⃣ Testar API (novo terminal)

```bash
# Opção A: Script Python (recomendado)
python test_api.py

# Opção B: cURL manual
curl http://localhost:5000/health

# Opção C: Exemplo rápido
curl -X POST http://localhost:5000/api/notebooks \
  -H "Content-Type: application/json" \
  -d '{"title":"Meu Projeto"}'
```

---

## 📚 Documentação de Referência

| Arquivo | Conteúdo |
|---------|----------|
| `README.md` | Setup inicial + instruções |
| `ETAPA_2.md` | Documentação completa (services, rotas, padrões) |
| `API_TEST.md` | Exemplos de teste com cURL |
| `MODELS.md` | Documentação dos models SQLAlchemy |

---

## 🔌 Arquitetura (ETAPA 2)

```
REQUEST (HTTP)
    ↓
BLUEPRINT (routes/*.py)
    ↓
SERVICE (services/*.py)
    ↓
MODEL (models/*.py)
    ↓
DATABASE (SQLAlchemy)
    ↓
RESPONSE (APIResponse)
```

### Exemplo: Criar Notebook

```
POST /api/notebooks
  ↓
notebooks_blueprint.create_notebook()
  ↓
NotebookService.create_notebook()
  ↓
Notebook.query → db.session.commit()
  ↓
APIResponse.success()
  ↓
HTTP 201 + JSON
```

---

## 🎯 Rotas Disponíveis

### Notebooks
```
POST   /api/notebooks                 → Criar
GET    /api/notebooks                 → Listar (paginado)
GET    /api/notebooks/{id}            → Obter + stats
PUT    /api/notebooks/{id}            → Atualizar
DELETE /api/notebooks/{id}            → Deletar
```

### Cells
```
POST   /api/notebooks/{id}/cells                → Criar
GET    /api/notebooks/{id}/cells                → Listar (ordenadas)
GET    /api/notebooks/{id}/cells/{id}           → Obter
PUT    /api/notebooks/{id}/cells/{id}           → Atualizar
DELETE /api/notebooks/{id}/cells/{id}           → Deletar
POST   /api/notebooks/{id}/cells/reorder        → Reordenar
```

### Executions
```
POST   /api/notebooks/{id}/cells/{id}/execute       → Iniciar
PUT    /api/notebooks/{id}/executions/{id}          → Atualizar
GET    /api/notebooks/{id}/cells/{id}/executions    → Histórico
GET    /api/notebooks/{id}/executions               → Todas
GET    /api/notebooks/{id}/cells/{id}/stats         → Stats
```

---

## 🧪 Teste Completo (Fluxo Real)

```bash
#!/bin/bash

# 1. Criar notebook
NOTEBOOK=$(curl -s -X POST http://localhost:5000/api/notebooks \
  -H "Content-Type: application/json" \
  -d '{"title":"Teste"}' | jq -r '.data.id')

echo "📌 Notebook: $NOTEBOOK"

# 2. Criar célula
CELL=$(curl -s -X POST http://localhost:5000/api/notebooks/$NOTEBOOK/cells \
  -H "Content-Type: application/json" \
  -d '{"cell_type":"code","content":"print(42)"}' | jq -r '.data.id')

echo "📍 Cell: $CELL"

# 3. Executar
EXEC=$(curl -s -X POST http://localhost:5000/api/notebooks/$NOTEBOOK/cells/$CELL/execute \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.data.id')

echo "⚙️  Execution: $EXEC"

# 4. Resultado
curl -s -X PUT http://localhost:5000/api/notebooks/$NOTEBOOK/executions/$EXEC \
  -H "Content-Type: application/json" \
  -d '{
    "status":"success",
    "execution_time":0.05,
    "logs":"42"
  }' | jq .

# 5. Ver stats
curl -s http://localhost:5000/api/notebooks/$NOTEBOOK/cells/$CELL/stats | jq .data
```

---

## 📊 Estrutura de Resposta Padrão

### ✅ Sucesso (2xx)
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "...",
    ...
  },
  "message": "Operação bem sucedida"
}
```

### ❌ Erro (4xx/5xx)
```json
{
  "success": false,
  "error": "Descrição do erro",
  "status_code": 400,
  "validation_errors": {
    "field": "Mensagem"
  }
}
```

---

## 🔐 Autorização (MVP)

Atualmente **hardcoded `user_id=1`** para facilitar testes.

Antes de produção, implementar:
- JWT authentication
- Middleware de auth
- Roles/permissões

---

## 🚨 Troubleshooting

### Servidor não inicia
```bash
# Verificar se porta 5000 está livre
lsof -i :5000

# Ou usar porta diferente
PORT=5001 python run.py
```

### Erro de banco de dados
```bash
# Reset completo
rm -rf migrations/
rm instance/indatalab.db
flask db init
flask db migrate -m "Initial"
flask db upgrade
```

### Erro de imports
```bash
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Groq API não funciona
```bash
# Verificar .env
cat .env | grep GROQ_API_KEY

# Deve estar preenchido
GROQ_API_KEY=gsk_seu_key_aqui
```

---

## 📁 Arquivos Novos (ETAPA 2)

```
app/
├── services/
│   ├── notebook_service.py  (165 linhas)
│   ├── cell_service.py      (287 linhas)
│   └── execution_service.py (310 linhas)
├── routes/
│   ├── notebooks_blueprint.py    (138 linhas)
│   ├── cells_blueprint.py        (163 linhas)
│   └── executions_blueprint.py   (200 linhas)
└── utils.py                  (228 linhas)

+ test_api.py                 (410 linhas)
+ API_TEST.md
+ ETAPA_2.md
```

**Total**: ~1,800 linhas de código + documentação

---

## ✨ Características Implementadas

### Services
- ✅ CRUD completo para notebooks e células
- ✅ Validação de entrada
- ✅ Autorização (user owns resource)
- ✅ Paginação
- ✅ Estatísticas e agregações
- ✅ Reordenação automática
- ✅ Error handling robusto

### Routes
- ✅ JSON API RESTful
- ✅ Response padrão
- ✅ HTTP status codes corretos
- ✅ Validação em dois níveis (route + service)
- ✅ 404/500 handlers

### Code Quality
- ✅ Type hints (Python 3.9+)
- ✅ Docstrings completas
- ✅ Separação de responsabilidades
- ✅ DRY (Don't Repeat Yourself)
- ✅ Sem lógica nas rotas

---

## 🎓 Conceitos Aplicados

| Padrão | Onde | Por quê |
|--------|------|--------|
| **Factory** | `create_app()` | Criação flexível da app |
| **Blueprint** | `routes/*.py` | Modularizar rotas |
| **Service** | `services/*.py` | Isolar lógica negócio |
| **Validation** | `utils.py` | Centralizar validação |
| **Response** | `APIResponse` | Padrão JSON |
| **Pagination** | Services | Escalabilidade |

---

## 🚀 Próxima Etapa: ETAPA 3

### Notebook Engine
- Python executor isolado
- DuckDB integração
- Output streaming
- Kernel management
- Timeout handling

### Auth
- JWT implementation
- Login/register routes
- User context

### Frontend (bônus)
- Web UI (React/HTML)
- Cell editor
- Real-time execution

---

## 📞 Support

Se tiver dúvidas:

1. Verificar `ETAPA_2.md` (documentação completa)
2. Executar `test_api.py` (valida tudo)
3. Testar endpoints manualmente com cURL
4. Checar logs do servidor (`python run.py`)

---

## 📝 Checklist de Validação

- [ ] Servidor inicia sem erros
- [ ] `/health` retorna 200
- [ ] Consegue criar notebook
- [ ] Consegue criar célula
- [ ] Consegue executar célula
- [ ] Stats são calculadas corretamente
- [ ] Deletar célula reordena posições
- [ ] `test_api.py` passa todos os testes

---

**Dione Castro Alves | InNovaIdeia | 2025**

Status: ✅ **ETAPA 2 - COMPLETA E TESTADA**

Next: 🔧 **ETAPA 3 - Python Executor + DuckDB**
