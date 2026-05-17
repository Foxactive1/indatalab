"""
InDataLab - Test Script
Testa a API completa (ETAPA 2)
Executa fluxo full: create notebook → cells → execution → stats
"""

import requests
import json
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:5000/api"


class APITester:
    """Tester para API InDataLab"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        self.notebook_id: Optional[int] = None
        self.cell_ids: list = []
        self.execution_ids: list = []
    
    def _print_response(self, title: str, response: Dict[str, Any], color: str = "\033[92m"):
        """Print formatado da resposta"""
        print(f"\n{color}{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\033[0m")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    
    def test_notebook_create(self) -> bool:
        """Teste: Criar notebook"""
        print("\n\n🔵 TEST 1: Criar Notebook")
        
        try:
            resp = self.session.post(
                f"{self.base_url}/notebooks",
                json={
                    "title": "InDataLab Test Notebook",
                    "description": "Teste automático ETAPA 2",
                    "is_public": False,
                    "kernel_type": "python3"
                }
            )
            
            data = resp.json()
            self._print_response("POST /notebooks", data)
            
            if data.get('success'):
                self.notebook_id = data['data']['id']
                print(f"\n✅ Notebook criado: ID = {self.notebook_id}")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def test_notebook_list(self) -> bool:
        """Teste: Listar notebooks"""
        print("\n\n🔵 TEST 2: Listar Notebooks")
        
        try:
            resp = self.session.get(f"{self.base_url}/notebooks")
            data = resp.json()
            self._print_response("GET /notebooks", data)
            
            if data.get('success'):
                count = len(data['data']['notebooks'])
                print(f"\n✅ {count} notebook(s) listado(s)")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def test_notebook_get(self) -> bool:
        """Teste: Obter notebook com stats"""
        print(f"\n\n🔵 TEST 3: Obter Notebook (ID={self.notebook_id})")
        
        if not self.notebook_id:
            print("❌ Notebook não criado antes")
            return False
        
        try:
            resp = self.session.get(f"{self.base_url}/notebooks/{self.notebook_id}")
            data = resp.json()
            self._print_response(f"GET /notebooks/{self.notebook_id}", data)
            
            if data.get('success'):
                stats = data['data'].get('stats', {})
                print(f"\n✅ Stats do notebook:")
                print(f"   - Células: {stats.get('cell_count', 0)}")
                print(f"   - Execuções: {stats.get('total_executions', 0)}")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def test_cell_create_code(self) -> bool:
        """Teste: Criar célula de código"""
        print(f"\n\n🔵 TEST 4: Criar Célula (Code)")
        
        if not self.notebook_id:
            print("❌ Notebook não criado antes")
            return False
        
        try:
            resp = self.session.post(
                f"{self.base_url}/notebooks/{self.notebook_id}/cells",
                json={
                    "cell_type": "code",
                    "content": "import pandas as pd\nprint('InDataLab v0.1')",
                    "tags": "importação,teste"
                }
            )
            
            data = resp.json()
            self._print_response("POST /cells", data)
            
            if data.get('success'):
                cell_id = data['data']['id']
                self.cell_ids.append(cell_id)
                print(f"\n✅ Célula criada: ID = {cell_id}")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def test_cell_create_markdown(self) -> bool:
        """Teste: Criar célula de markdown"""
        print(f"\n\n🔵 TEST 5: Criar Célula (Markdown)")
        
        if not self.notebook_id:
            print("❌ Notebook não criado antes")
            return False
        
        try:
            resp = self.session.post(
                f"{self.base_url}/notebooks/{self.notebook_id}/cells",
                json={
                    "cell_type": "markdown",
                    "content": "# Análise de Dados\n\nEste notebook testa..."
                }
            )
            
            data = resp.json()
            self._print_response("POST /cells (markdown)", data)
            
            if data.get('success'):
                cell_id = data['data']['id']
                self.cell_ids.append(cell_id)
                print(f"\n✅ Célula markdown criada: ID = {cell_id}")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def test_cell_list(self) -> bool:
        """Teste: Listar células"""
        print(f"\n\n🔵 TEST 6: Listar Células")
        
        if not self.notebook_id:
            print("❌ Notebook não criado antes")
            return False
        
        try:
            resp = self.session.get(
                f"{self.base_url}/notebooks/{self.notebook_id}/cells"
            )
            
            data = resp.json()
            self._print_response("GET /cells", data)
            
            if data.get('success'):
                count = len(data['data']['cells'])
                print(f"\n✅ {count} célula(s) listada(s)")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def test_execution_create(self) -> bool:
        """Teste: Criar execução"""
        print(f"\n\n🔵 TEST 7: Criar Execução")
        
        if not self.notebook_id or not self.cell_ids:
            print("❌ Notebook/Célula não criado(a) antes")
            return False
        
        cell_id = self.cell_ids[0]
        
        try:
            resp = self.session.post(
                f"{self.base_url}/notebooks/{self.notebook_id}/cells/{cell_id}/execute",
                json={"status": "running"}
            )
            
            data = resp.json()
            self._print_response("POST /execute", data)
            
            if data.get('success'):
                exec_id = data['data']['id']
                self.execution_ids.append(exec_id)
                print(f"\n✅ Execução criada: ID = {exec_id}")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def test_execution_update(self) -> bool:
        """Teste: Atualizar execução com resultado"""
        print(f"\n\n🔵 TEST 8: Atualizar Execução (com resultado)")
        
        if not self.notebook_id or not self.execution_ids:
            print("❌ Execução não criada antes")
            return False
        
        exec_id = self.execution_ids[0]
        
        try:
            resp = self.session.put(
                f"{self.base_url}/notebooks/{self.notebook_id}/executions/{exec_id}",
                json={
                    "status": "success",
                    "execution_time": 0.123,
                    "logs": "InDataLab v0.1\n✅ Test passed",
                    "memory_used": 15.4
                }
            )
            
            data = resp.json()
            self._print_response("PUT /executions/{id}", data)
            
            if data.get('success'):
                print(f"\n✅ Execução atualizada com sucesso")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def test_execution_stats(self) -> bool:
        """Teste: Obter stats de execução"""
        print(f"\n\n🔵 TEST 9: Obter Stats de Execução")
        
        if not self.notebook_id or not self.cell_ids:
            print("❌ Célula não criada antes")
            return False
        
        cell_id = self.cell_ids[0]
        
        try:
            resp = self.session.get(
                f"{self.base_url}/notebooks/{self.notebook_id}/cells/{cell_id}/stats"
            )
            
            data = resp.json()
            self._print_response(f"GET /cells/{cell_id}/stats", data)
            
            if data.get('success'):
                stats = data['data']
                print(f"\n✅ Stats obtidos:")
                print(f"   - Total execuções: {stats.get('total_executions')}")
                print(f"   - Sucesso: {stats.get('successful')}")
                print(f"   - Erros: {stats.get('errors')}")
                print(f"   - Taxa sucesso: {stats.get('success_rate')}%")
                print(f"   - Tempo médio: {stats.get('avg_execution_time')}s")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def test_notebook_update(self) -> bool:
        """Teste: Atualizar notebook"""
        print(f"\n\n🔵 TEST 10: Atualizar Notebook")
        
        if not self.notebook_id:
            print("❌ Notebook não criado antes")
            return False
        
        try:
            resp = self.session.put(
                f"{self.base_url}/notebooks/{self.notebook_id}",
                json={
                    "title": "InDataLab Test Notebook [UPDATED]",
                    "is_public": True
                }
            )
            
            data = resp.json()
            self._print_response("PUT /notebooks/{id}", data)
            
            if data.get('success'):
                print(f"\n✅ Notebook atualizado")
                return True
            else:
                print(f"\n❌ Erro: {data.get('error')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            return False
    
    def run_all_tests(self) -> None:
        """Executar todos os testes"""
        print("\n" + "="*60)
        print("  🧪 InDataLab - ETAPA 2 - Full Test Suite")
        print("="*60)
        
        tests = [
            ("Criar Notebook", self.test_notebook_create),
            ("Listar Notebooks", self.test_notebook_list),
            ("Obter Notebook", self.test_notebook_get),
            ("Criar Célula (Code)", self.test_cell_create_code),
            ("Criar Célula (Markdown)", self.test_cell_create_markdown),
            ("Listar Células", self.test_cell_list),
            ("Criar Execução", self.test_execution_create),
            ("Atualizar Execução", self.test_execution_update),
            ("Obter Stats", self.test_execution_stats),
            ("Atualizar Notebook", self.test_notebook_update),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"\n❌ ERRO em {test_name}: {str(e)}")
                results.append((test_name, False))
        
        # Resumo
        print("\n\n" + "="*60)
        print("  📊 RESUMO DE TESTES")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\n{'='*60}")
        print(f"Total: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM!")
        else:
            print(f"⚠️  {total - passed} teste(s) falharam")
        
        print("="*60 + "\n")


if __name__ == "__main__":
    import sys
    
    print("\n🚀 Iniciando testes da API InDataLab...")
    print("📍 Base URL:", BASE_URL)
    
    # Check se servidor está rodando
    try:
        resp = requests.get(f"{BASE_URL.replace('/api', '')}/health")
        if resp.status_code != 200:
            print("\n❌ Servidor não está respondendo em /health")
            print("   Execute 'python run.py' em outro terminal")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Não consigo conectar ao servidor")
        print("   Execute 'python run.py' em outro terminal")
        sys.exit(1)
    
    # Rodar testes
    tester = APITester(BASE_URL)
    tester.run_all_tests()
