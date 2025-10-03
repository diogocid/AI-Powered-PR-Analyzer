import os
import json
from dotenv import load_dotenv

class AIAnalyzer:
    """Analisa dados formatados usando IA (Claude, OpenAI ou Ollama) para gerar documentação"""

    def __init__(self):
        load_dotenv()

        # Tentar determinar qual API usar
        self.provider = None
        self.client = None
        self.model = None

        # Opção 1: Claude (Anthropic)
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and anthropic_key != 'your_anthropic_api_key_here':
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=anthropic_key)
                self.model = "claude-3-5-sonnet-20250219"
                self.provider = "claude"
                print("[INFO] Usando Claude AI")
                return
            except ImportError:
                print("[AVISO] Anthropic nao instalado. Instala com: pip install anthropic")
            except Exception as e:
                print(f"[AVISO] Erro ao inicializar Claude: {e}")

        # Opção 2: OpenAI (GPT)
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key != 'your_openai_api_key_here':
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=openai_key)
                self.model = "gpt-4o"
                self.provider = "openai"
                print("[INFO] Usando OpenAI GPT-4")
                return
            except ImportError:
                print("[AVISO] OpenAI nao instalado. Instala com: pip install openai")
            except Exception as e:
                print(f"[AVISO] Erro ao inicializar OpenAI: {e}")

        # Opção 3: Ollama (Local, grátis)
        try:
            import requests
            # Testar se Ollama está rodando
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200:
                self.provider = "ollama"
                self.model = "llama3.2:3b"  # Modelo mais rápido
                print("[INFO] Usando Ollama (local)")
                print(f"[INFO] Modelo: {self.model} (versao rapida)")
                return
        except ImportError:
            print("[AVISO] Requests nao instalado. Instala com: pip install requests")
        except:
            pass

        # Nenhuma opção disponível
        raise ValueError(
            "\n[ERRO] Nenhum provedor de IA configurado!\n\n"
            "Opcoes disponiveis:\n\n"
            "1. CLAUDE (Anthropic):\n"
            "   - Obtem key em: https://console.anthropic.com/\n"
            "   - Adiciona ao .env: ANTHROPIC_API_KEY=sua_key_aqui\n"
            "   - Instala: pip install anthropic\n\n"
            "2. OPENAI (GPT-4):\n"
            "   - Obtem key em: https://platform.openai.com/api-keys\n"
            "   - Adiciona ao .env: OPENAI_API_KEY=sua_key_aqui\n"
            "   - Instala: pip install openai\n\n"
            "3. OLLAMA (Local - GRATIS):\n"
            "   - Baixa em: https://ollama.com/download\n"
            "   - Instala e executa: ollama pull llama3.1\n"
            "   - Inicia: ollama serve\n"
            "   - Instala: pip install requests\n"
        )

    def load_json_files(self):
        """Carrega todos os ficheiros issue_*.json e pr_*.json"""
        data = {}

        try:
            # Carregar ficheiros issue_*.json
            for filename in os.listdir('.'):
                if filename.startswith('issue_') and filename.endswith('.json'):
                    with open(filename, 'r', encoding='utf-8') as f:
                        data[filename] = json.load(f)
                        print(f"[OK] Carregado: {filename}")

                # Carregar ficheiros pr_*.json
                elif filename.startswith('pr_') and filename.endswith('.json'):
                    with open(filename, 'r', encoding='utf-8') as f:
                        data[filename] = json.load(f)
                        print(f"[OK] Carregado: {filename}")

            return data if data else None
        except Exception as e:
            print(f"[ERRO] Erro ao carregar ficheiros: {e}")
            return None

    def _truncate_text(self, text, max_chars=100000):
        """Trunca texto para evitar exceder limites de tokens"""
        #if len(text) > max_chars:
        #    return text[:max_chars] + "\n\n[... CONTEUDO TRUNCADO ...]"
        return text

    def create_documentation_prompt(self, data):
        """Cria prompt para gerar documentação"""

        # Truncar dados se necessário
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        formatted_json = self._truncate_text(formatted_json, max_chars=80000)

        prompt = f"""Analisa os seguintes dados de uma issue do Jira (se disponível) e um Pull Request do Azure DevOps e gera documentação técnica completa e profissional.

# DADOS ESTRUTURADOS
{formatted_json}

# TAREFA
Gera documentação técnica clara e profissional baseada nas alterações do código. A documentação deve ser adaptada ao tipo de mudança (API, funcionalidade, bug fix, etc.).

## 📋 Estrutura da Documentação

### 1. **Resumo**
- Título descritivo da funcionalidade/alteração
- Breve descrição (2-3 frases) do que foi implementado/alterado

### 2. **Contexto** (se aplicável)
- Objetivo da mudança
- Problema que resolve
- Relação com a issue do Jira (se disponível)

### 3. **Detalhes Técnicos**
Adapta conforme o tipo de alteração:

**Para APIs/Endpoints:**
- Método HTTP e endpoint
- Parâmetros de entrada (com tipos e descrições)
- Formato de resposta
- Códigos de status HTTP
- Exemplos de request/response

**Para Funcionalidades:**
- Como usar a funcionalidade
- Configurações necessárias
- Dependências
- Exemplos de código

**Para Bug Fixes:**
- Descrição do bug corrigido
- Causa raiz identificada
- Solução implementada

### 4. **Exemplos de Uso** (se aplicável)
```
[Exemplos práticos baseados no código do PR]
```

### 5. **Notas Adicionais** (se aplicável)
- Limitações conhecidas
- Considerações de performance
- Breaking changes
- Migrações necessárias

IMPORTANTE:
- Adapta a estrutura ao contexto das alterações
- Usa exemplos reais do código alterado
- Mantém linguagem clara e profissional
- Formata em Markdown
- Usa emojis moderadamente nos títulos para melhor visualização"""

        return prompt

    def _call_ai(self, prompt, max_tokens=8000):
        """Chama a IA apropriada (Claude, OpenAI ou Ollama)"""

        if self.provider == "claude":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        elif self.provider == "ollama":
            import requests
            print("[INFO] Chamando Ollama (pode demorar 2-5 minutos)...")
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3
                    }
                },
                timeout=600  # 10 minutos
            )
            print("[INFO] Resposta recebida!")
            return response.json()['response']

        else:
            raise ValueError("Nenhum provedor de IA configurado")

    def generate_documentation(self, data=None):
        """Gera documentação usando IA"""

        # Carregar dados se não fornecidos
        if not data:
            data = self.load_json_files()
            if not data:
                print("[ERRO] Nenhum ficheiro issue_*.json ou pr_*.json encontrado")
                return None

        print(f"Gerando documentacao com {self.provider.upper()}...")
        print(f"Modelo: {self.model}")
        print("Aguarda enquanto a IA analisa o codigo...\n")

        # Criar prompt
        prompt = self.create_documentation_prompt(data)

        try:
            documentation = self._call_ai(prompt, max_tokens=8000)
            print("[OK] Documentacao gerada com sucesso!")
            return documentation

        except Exception as e:
            print(f"[ERRO] Erro ao gerar documentacao: {e}")
            return None

    def generate_code_review(self, data=None):
        """Gera code review detalhado das alterações"""

        if not data:
            data = self.load_json_files()
            if not data:
                print("[ERRO] Nenhum ficheiro issue_*.json ou pr_*.json encontrado")
                return None

        print(f"\nGerando code review com {self.provider.upper()}...")

        # Criar prompt específico para code review (truncar dados)
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        formatted_json = self._truncate_text(formatted_json, max_chars=80000)

        prompt = f"""Analisa as seguintes alterações de código e fornece um code review detalhado e construtivo.
no final dá-me sugestões do que pode ser mudado, procura também variáveis com erros  ou pouca leitura
# DADOS DO PULL REQUEST
{formatted_json}

# TAREFA
Fornece um code review profissional que inclua:

1. **Resumo das Alterações**
   - O que foi alterado
   - Impacto das mudanças

2. **Análise de Qualidade**
   - Qualidade do código
   - Padrões seguidos
   - Boas práticas aplicadas

3. **Potenciais Problemas**
   - Bugs potenciais identificados
   - Problemas de performance
   - Questões de segurança
   - Edge cases não considerados

4. **Sugestões de Melhoria**
   - Refactoring sugerido
   - Otimizações possíveis
   - Melhorias de legibilidade

5. **Aprovação**
   - Recomendação final (Aprovar / Aprovar com sugestões / Requer mudanças)
   - Justificação

Formata em **Markdown** de forma clara e profissional."""

        try:
            review = self._call_ai(prompt, max_tokens=6000)
            print("[OK] Code review gerado com sucesso!")
            return review

        except Exception as e:
            print(f"[ERRO] Erro ao gerar code review: {e}")
            return None

    def save_documentation(self, documentation, filename='DOCUMENTATION.md'):
        """Salva documentação em ficheiro"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(documentation)
            print(f"\nDocumentacao salva em {filename}")
            return True
        except Exception as e:
            print(f"[ERRO] Erro ao salvar documentacao: {e}")
            return False

    def save_code_review(self, review, filename='CODE_REVIEW.md'):
        """Salva code review em ficheiro"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(review)
            print(f"Code review salvo em {filename}")
            return True
        except Exception as e:
            print(f"[ERRO] Erro ao salvar code review: {e}")
            return False


if __name__ == "__main__":
    print("="*80)
    print("GERADOR DE DOCUMENTACAO COM IA")
    print("="*80)
    print()

    try:
        # Inicializar analisador
        analyzer = AIAnalyzer()

        # Gerar documentação técnica
        documentation = analyzer.generate_documentation()
        if documentation:
            analyzer.save_documentation(documentation)
            print("\n" + "="*80)
            print("PREVIEW DA DOCUMENTACAO")
            print("="*80)
            print(documentation[:500] + "...\n")

        # Gerar code review
        review = analyzer.generate_code_review()
        if review:
            analyzer.save_code_review(review)
            print("\n" + "="*80)
            print("PREVIEW DO CODE REVIEW")
            print("="*80)
            print(review[:500] + "...\n")

        print("\n" + "="*80)
        print("CONCLUIDO!")
        print("="*80)
        print("Ficheiros gerados:")
        print("  - DOCUMENTATION.md (Documentacao tecnica completa)")
        print("  - CODE_REVIEW.md (Code review detalhado)")

    except ValueError as e:
        print(f"\n{e}")
    except Exception as e:
        print(f"\n[ERRO] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
