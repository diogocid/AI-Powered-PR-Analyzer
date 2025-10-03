import os
import json
from jira_client import JiraClient
from azdo_client import AzureDevOpsClient
from ai_analyzer import AIAnalyzer

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Dados obrigatórios do PR
REPO = "MyRepository"  # Nome do repositório Azure DevOps
PR_ID = 12345  # ID do Pull Request

# Dados opcionais da issue (deixar None se não houver issue associada)
ISSUE_KEY = None  # Key da issue do Jira (ex: "PROJ-123") ou None

# O que gerar (True/False)
GENERATE_DOCUMENTATION = True  # Gerar documentação técnica
GENERATE_CODE_REVIEW = True    # Gerar code review

# Prompts personalizados (opcional - deixar None para usar os padrões)
CUSTOM_CODE_REVIEW_PROMPT = None  # Exemplo: "Analisa o código focando em performance e segurança..."
CUSTOM_DOCUMENTATION_PROMPT = None  # Exemplo: "Gera documentação focada em APIs REST..."

# Exemplos de prompts personalizados (descomente para usar):

# CUSTOM_CODE_REVIEW_PROMPT = """
# Analisa o código do PR com foco especial em:
# - Performance e otimizações
# - Segurança e validações
# - Testes unitários
# Fornece um relatório detalhado em português.
# """

# CUSTOM_DOCUMENTATION_PROMPT = """
# Gera documentação técnica no formato OpenAPI/Swagger para APIs REST.
# Inclui:
# - Endpoints
# - Métodos HTTP
# - Request/Response schemas
# - Códigos de erro
# """

# ============================================================================

class WorkflowOrchestrator:
    """Orquestrador que une Jira, Azure DevOps e AI Analyzer"""

    def __init__(self, repo, pr_id, issue_key=None,
                 generate_documentation=True,
                 generate_code_review=True,
                 code_review_prompt=None,
                 documentation_prompt=None):
        """
        Inicializa o orquestrador

        Args:
            repo (str): Nome do repositório no Azure DevOps
            pr_id (int): ID do Pull Request
            issue_key (str, optional): Key da issue do Jira (ex: PROJ-123). Pode ser None.
            generate_documentation (bool): Se True, gera documentação técnica
            generate_code_review (bool): Se True, gera code review
            code_review_prompt (str, optional): Prompt personalizado para code review
            documentation_prompt (str, optional): Prompt personalizado para documentação
        """
        self.repo = repo
        self.pr_id = pr_id
        self.issue_key = issue_key
        self.generate_documentation = generate_documentation
        self.generate_code_review = generate_code_review
        self.custom_code_review_prompt = code_review_prompt
        self.custom_documentation_prompt = documentation_prompt

        # Inicializar clients
        self.jira_client = JiraClient() if issue_key else None
        self.azdo_client = AzureDevOpsClient()
        self.ai_analyzer = AIAnalyzer() if (generate_documentation or generate_code_review) else None

    def fetch_issue_data(self):
        """Busca dados da issue do Jira (se houver)"""
        if not self.issue_key:
            print(f"\n{'='*80}")
            print(f"1. SEM ISSUE DO JIRA (OPCIONAL)")
            print(f"{'='*80}")
            print("⊘ Issue key não fornecida - continuando sem dados do Jira")
            return None

        print(f"\n{'='*80}")
        print(f"1. BUSCANDO ISSUE DO JIRA: {self.issue_key}")
        print(f"{'='*80}")

        issue_data = self.jira_client.get_issue_summary_only(self.issue_key)

        if issue_data:
            print(f"✓ Issue encontrada: {issue_data['key']}")
            print(f"  Summary: {issue_data['summary']}")

            # Salvar em ficheiro
            with open('issue_data.json', 'w', encoding='utf-8') as f:
                json.dump(issue_data, f, indent=4, ensure_ascii=False)
            print("✓ issue_data.json criado")
            return issue_data
        else:
            print("✗ Erro ao buscar issue")
            return None

    def fetch_pr_data(self):
        """Busca dados do Pull Request do Azure DevOps"""
        print(f"\n{'='*80}")
        print(f"2. BUSCANDO PULL REQUEST: #{self.pr_id} (repo: {self.repo})")
        print(f"{'='*80}")

        # Buscar commits
        print("\n[1/2] Buscando commits do PR...")
        commits_data = self.azdo_client.get_pr_commits(self.repo, self.pr_id)

        if commits_data:
            commits_list = commits_data.get('value', [])
            print(f"✓ Total de commits: {len(commits_list)}")

            with open('pr_commits.json', 'w', encoding='utf-8') as f:
                json.dump(commits_data, f, indent=4, ensure_ascii=False)
            print("✓ pr_commits.json criado")
        else:
            print("✗ Erro ao buscar commits")
            return None

        # Buscar ficheiros alterados
        print("\n[2/2] Buscando linhas adicionadas nos ficheiros do PR...")
        added_lines_data = self.azdo_client.get_pr_added_lines_only(self.repo, self.pr_id)

        if added_lines_data:
            print(f"✓ Total de ficheiros com alterações: {added_lines_data['total']}")

            with open('pr_files_content.json', 'w', encoding='utf-8') as f:
                json.dump(added_lines_data, f, indent=4, ensure_ascii=False)
            print("✓ pr_files_content.json criado")

            # Mostrar resumo
            print("\nResumo das linhas adicionadas:")
            for file_info in added_lines_data.get('files', [])[:5]:  # Mostrar apenas 5 primeiros
                print(f"  • {file_info['path']}: {len(file_info['added_lines'])} linhas")

            if added_lines_data['total'] > 5:
                print(f"  ... e mais {added_lines_data['total'] - 5} ficheiros")

            return added_lines_data
        else:
            print("✗ Erro ao buscar ficheiros do PR")
            return None

    def _generate_documentation(self):
        """Gera documentação usando AI"""
        print(f"\n{'='*80}")
        print(f"3. GERANDO DOCUMENTAÇÃO COM IA")
        print(f"{'='*80}")

        # Se houver prompt personalizado, substitui no AIAnalyzer
        if self.custom_documentation_prompt:
            print("[INFO] Usando prompt personalizado para documentação")
            # Sobrescrever método create_documentation_prompt temporariamente
            original_method = self.ai_analyzer.create_documentation_prompt

            def custom_prompt_wrapper(data):
                formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                formatted_json = self.ai_analyzer._truncate_text(formatted_json, max_chars=80000)
                return f"{self.custom_documentation_prompt}\n\n# DADOS ESTRUTURADOS\n{formatted_json}"

            self.ai_analyzer.create_documentation_prompt = custom_prompt_wrapper

        documentation = self.ai_analyzer.generate_documentation()

        if documentation:
            self.ai_analyzer.save_documentation(documentation)
            print("\n[PREVIEW] Primeiras linhas da documentação:")
            print("-" * 80)
            print(documentation[:400] + "...")
            print("-" * 80)
            return documentation
        else:
            print("✗ Erro ao gerar documentação")
            return None

    def _generate_code_review(self):
        """Gera code review usando AI"""
        print(f"\n{'='*80}")
        print(f"4. GERANDO CODE REVIEW COM IA")
        print(f"{'='*80}")

        # Se houver prompt personalizado, substitui
        if self.custom_code_review_prompt:
            print("[INFO] Usando prompt personalizado para code review")

            # Carregar dados
            data = self.ai_analyzer.load_json_files()
            if not data:
                print("[ERRO] Nenhum ficheiro de dados encontrado")
                return None

            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            formatted_json = self.ai_analyzer._truncate_text(formatted_json, max_chars=80000)

            custom_prompt = f"{self.custom_code_review_prompt}\n\n# DADOS DO PULL REQUEST\n{formatted_json}"

            try:
                review = self.ai_analyzer._call_ai(custom_prompt, max_tokens=6000)
                print("[OK] Code review gerado com sucesso!")
                self.ai_analyzer.save_code_review(review)

                print("\n[PREVIEW] Primeiras linhas do code review:")
                print("-" * 80)
                print(review[:400] + "...")
                print("-" * 80)
                return review
            except Exception as e:
                print(f"[ERRO] Erro ao gerar code review: {e}")
                return None
        else:
            # Usar método padrão
            review = self.ai_analyzer.generate_code_review()

            if review:
                self.ai_analyzer.save_code_review(review)
                print("\n[PREVIEW] Primeiras linhas do code review:")
                print("-" * 80)
                print(review[:400] + "...")
                print("-" * 80)
                return review
            else:
                print("✗ Erro ao gerar code review")
                return None

    def run(self):
        """Executa o fluxo completo"""
        print("\n" + "="*80)
        print("WORKFLOW AUTOMÁTICO - JIRA + AZURE DEVOPS + IA")
        print("="*80)
        print(f"\nConfiguração:")
        print(f"  • Issue Jira: {self.issue_key if self.issue_key else 'N/A (opcional)'}")
        print(f"  • Repositório: {self.repo}")
        print(f"  • Pull Request: #{self.pr_id}")
        print(f"  • Gerar documentação: {'Sim' if self.generate_documentation else 'Não'}")
        print(f"  • Gerar code review: {'Sim' if self.generate_code_review else 'Não'}")
        print(f"  • Prompt custom code review: {'Sim' if self.custom_code_review_prompt else 'Não (usa padrão)'}")
        print(f"  • Prompt custom documentação: {'Sim' if self.custom_documentation_prompt else 'Não (usa padrão)'}")

        # 1. Buscar issue (opcional)
        issue_data = self.fetch_issue_data()
        # Não falha se não houver issue - continua apenas com PR

        # 2. Buscar PR (obrigatório)
        pr_data = self.fetch_pr_data()
        if not pr_data:
            print("\n[ERRO] Não foi possível continuar sem dados do PR")
            return False

        # 3. Gerar documentação (se ativado)
        documentation = None
        if self.generate_documentation:
            documentation = self._generate_documentation()
        else:
            print(f"\n{'='*80}")
            print(f"3. DOCUMENTAÇÃO DESATIVADA")
            print(f"{'='*80}")
            print("⊘ Geração de documentação desativada nas configurações")

        # 4. Gerar code review (se ativado)
        code_review = None
        if self.generate_code_review:
            code_review = self._generate_code_review()
        else:
            print(f"\n{'='*80}")
            print(f"4. CODE REVIEW DESATIVADO")
            print(f"{'='*80}")
            print("⊘ Geração de code review desativada nas configurações")

        # Resumo final
        print(f"\n{'='*80}")
        print("✓ WORKFLOW CONCLUÍDO COM SUCESSO!")
        print(f"{'='*80}")
        print("\nFicheiros gerados:")
        if issue_data:
            print("  📄 issue_data.json - Dados da issue do Jira")
        print("  📄 pr_commits.json - Commits do Pull Request")
        print("  📄 pr_files_content.json - Ficheiros alterados no PR")
        if documentation:
            print("  📝 DOCUMENTATION.md - Documentação técnica gerada por IA")
        if code_review:
            print("  🔍 CODE_REVIEW.md - Code review gerado por IA")
        print()

        return True


if __name__ == "__main__":
    try:
        orchestrator = WorkflowOrchestrator(
            repo=REPO,
            pr_id=PR_ID,
            issue_key=ISSUE_KEY,  # Pode ser None
            generate_documentation=GENERATE_DOCUMENTATION,
            generate_code_review=GENERATE_CODE_REVIEW,
            code_review_prompt=CUSTOM_CODE_REVIEW_PROMPT,
            documentation_prompt=CUSTOM_DOCUMENTATION_PROMPT
        )

        orchestrator.run()

    except Exception as e:
        print(f"\n[ERRO CRÍTICO] {e}")
        import traceback
        traceback.print_exc()
