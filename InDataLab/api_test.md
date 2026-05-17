# InDataLab - ETAPA 2: Teste da API

## Setup Rápido

```bash
cd indatalab
source venv/bin/activate
python run.py
```

Servidor rodando em: `http://localhost:5000`

---

## Health Check

```bash
curl http://localhost:5000/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "service": "InDataLab API",
  "version": "0.1.0"
}
```

---

## 📝 NOTEBOOKS API

### 1. Criar Notebook

```bash
curl -X POST http://localhost:5000/api/notebooks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Análise de Vendas",
    "description": "Análise mensal de vendas",
    "is_public": false,
    "kernel_type": "python3"
  }'
```

Resposta:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": 1,
    "title": "Análise de Vendas",
    "description": "Análise mensal de vendas",
    "is_public": false,
    "kernel_type": "python3",
    "is_archived": false,
    "created_at": "2025-05-12T...",
    "updated_at": "2025-05-12T..."
  },
  "message": "Notebook criado com sucesso"
}
```

**Guarde o `id` retornado** — será usado nas próximas requisições.

### 2. Listar Notebooks (paginado)

```bash
curl http://localhost:5000/api/notebooks?page=1&per_page=20
```

### 3. Obter Notebook com Stats

```bash
curl http://localhost:5000/api/notebooks/1
```

Resposta (com estatísticas):
```json
{
  "success": true,
  "data": {
    "notebook": { ... },
    "stats": {
      "notebook_id": 1,
      "cell_count": 3,
      "code_cells": 2,
      "markdown_cells": 1,
      "total_executions": 5,
      "created_at": "...",
      "updated_at": "..."
    }
  }
}
```

### 4. Atualizar Notebook

```bash
curl -X PUT http://localhost:5000/api/notebooks/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Análise de Vendas 2025",
    "is_public": true
  }'
```

### 5. Deletar Notebook

```bash
curl -X DELETE http://localhost:5000/api/notebooks/1
```

---

## 📍 CELLS API

Substitua `{notebook_id}` pelo ID do notebook criado.

### 1. Criar Célula

```bash
curl -X POST http://localhost:5000/api/notebooks/1/cells \
  -H "Content-Type: application/json" \
  -d '{
    "cell_type": "code",
    "content": "import pandas as pd\ndf = pd.read_csv(\"data.csv\")",
    "position": 0,
    "tags": "importação,dados"
  }'
```

Resposta:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "notebook_id": 1,
    "cell_type": "code",
    "content": "import pandas as pd\ndf = pd.read_csv(\"data.csv\")",
    "position": 0,
    "execution_count": 0,
    "output": null,
    "created_at": "...",
    "updated_at": "..."
  },
  "message": "Célula criada"
}
```

### 2. Criar Célula Markdown

```bash
curl -X POST http://localhost:5000/api/notebooks/1/cells \
  -H "Content-Type: application/json" \
  -d '{
    "cell_type": "markdown",
    "content": "# Título\n\nDescrição da análise"
  }'
```

### 3. Listar Células (ordenadas)

```bash
# Todas as células
curl http://localhost:5000/api/notebooks/1/cells

# Apenas code cells
curl http://localhost:5000/api/notebooks/1/cells?cell_type=code

# Apenas markdown cells
curl http://localhost:5000/api/notebooks/1/cells?cell_type=markdown
```

### 4. Obter Célula

```bash
curl http://localhost:5000/api/notebooks/1/cells/1
```

### 5. Atualizar Célula

```bash
curl -X PUT http://localhost:5000/api/notebooks/1/cells/1 \
  -H "Content-Type: application/json" \
  -d '{
    "content": "print(\"hello world\")",
    "output": "hello world",
    "is_hidden": false
  }'
```

### 6. Deletar Célula

```bash
curl -X DELETE http://localhost:5000/api/notebooks/1/cells/1
```

### 7. Reordenar Células

```bash
curl -X POST http://localhost:5000/api/notebooks/1/cells/reorder \
  -H "Content-Type: application/json" \
  -d '{
    "cell_order": [3, 1, 2, 4]
  }'
```

---

## ⚙️ EXECUTIONS API

### 1. Criar Execução (iniciar)

```bash
curl -X POST http://localhost:5000/api/notebooks/1/cells/1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "status": "running"
  }'
```

Resposta (guarde o `id`):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "cell_id": 1,
    "status": "running",
    "execution_time": null,
    "logs": null,
    "error_message": null,
    "executed_at": "...",
    "created_at": "..."
  },
  "message": "Execução iniciada"
}
```

### 2. Atualizar Execução (após término)

```bash
curl -X PUT http://localhost:5000/api/notebooks/1/executions/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "success",
    "execution_time": 2.345,
    "logs": "resultado\nda\nexecução",
    "memory_used": 25.4
  }'
```

### 3. Executar com Erro

```bash
curl -X POST http://localhost:5000/api/notebooks/1/cells/1/execute \
  -H "Content-Type: application/json" \
  -d '{"status": "running"}'

# Depois, atualizar com erro
curl -X PUT http://localhost:5000/api/notebooks/1/executions/2 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "error",
    "execution_time": 1.234,
    "error_message": "NameError: name x is not defined",
    "stderr": "Traceback..."
  }'
```

### 4. Listar Execuções de uma Célula

```bash
curl http://localhost:5000/api/notebooks/1/cells/1/executions?page=1&limit=50
```

### 5. Listar Todas as Execuções do Notebook

```bash
curl http://localhost:5000/api/notebooks/1/executions?page=1&limit=100
```

### 6. Obter Stats de uma Célula

```bash
curl http://localhost:5000/api/notebooks/1/cells/1/stats
```

Resposta:
```json
{
  "success": true,
  "data": {
    "cell_id": 1,
    "total_executions": 5,
    "successful": 4,
    "errors": 1,
    "success_rate": 80.0,
    "avg_execution_time": 2.1,
    "last_execution": "2025-05-12T15:30:45",
    "last_status": "success"
  }
}
```

---

## 🧪 Fluxo Completo de Teste

```bash
# 1. Criar notebook
NOTEBOOK=$(curl -s -X POST http://localhost:5000/api/notebooks \
  -H "Content-Type: application/json" \
  -d '{"title":"Teste"}' | jq -r '.data.id')

echo "Notebook: $NOTEBOOK"

# 2. Criar célula
CELL=$(curl -s -X POST http://localhost:5000/api/notebooks/$NOTEBOOK/cells \
  -H "Content-Type: application/json" \
  -d '{"cell_type":"code","content":"print(1+1)"}' | jq -r '.data.id')

echo "Cell: $CELL"

# 3. Executar célula
EXEC=$(curl -s -X POST http://localhost:5000/api/notebooks/$NOTEBOOK/cells/$CELL/execute \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.data.id')

echo "Execution: $EXEC"

# 4. Atualizar com resultado
curl -s -X PUT http://localhost:5000/api/notebooks/$NOTEBOOK/executions/$EXEC \
  -H "Content-Type: application/json" \
  -d '{
    "status":"success",
    "execution_time":0.1,
    "logs":"2"
  }' | jq .

# 5. Ver stats
curl -s http://localhost:5000/api/notebooks/$NOTEBOOK/cells/$CELL/stats | jq .
```

---

## 📊 Estructura de Resposta Padrão

### Sucesso (2xx)
```json
{
  "success": true,
  "data": { ... },
  "message": "Operação bem sucedida"
}
```

### Erro (4xx/5xx)
```json
{
  "success": false,
  "error": "Descrição do erro",
  "status_code": 400,
  "validation_errors": {
    "field": "Mensagem de erro"
  }
}
```

---

## 🔍 Validações Implementadas

✅ **Notebooks**
- Título obrigatório (1-255 caracteres)
- Autorização (user owns notebook)
- Soft-delete ready (is_archived)

✅ **Cells**
- Tipo validado (code ou markdown)
- Conteúdo obrigatório
- Position auto-incrementada
- Reordenação automática ao deletar

✅ **Executions**
- Status validado (pending/running/success/error)
- Incremento de execution_count
- Timing e erro logging

---

## 🚀 Próximos Passos (ETAPA 3)

- [ ] Executor Python isolado
- [ ] Output cell stream em tempo real
- [ ] DuckDB integração
- [ ] Kernel management
- [ ] Autenticação real (JWT)

---

**Teste tudo e boa sorte! 🎉**
