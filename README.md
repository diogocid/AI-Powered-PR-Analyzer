# 🤖 AI-Powered PR Analyzer

Ferramenta automática que integra **Jira**, **Azure DevOps** e **IA** para gerar documentação técnica e code reviews de Pull Requests.

## 📋 Funcionalidades

- ✅ Busca automática de issues do Jira
- ✅ Análise de Pull Requests do Azure DevOps
- ✅ Geração de documentação técnica com IA
- ✅ Code review automático detalhado
- ✅ Prompts personalizáveis
- ✅ Suporte para Claude, OpenAI GPT-4 e Ollama (local)

## 🚀 Instalação

### 1. Clonar o repositório
```bash
git clone <repository-url>
cd Hackforimpact
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Cria um ficheiro `.env` na raiz do projeto:

```env
# Jira (opcional)
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token

# Azure DevOps
AZDO_ORGANIZATION=your-organization
AZDO_PROJECT=your-project
AZDO_PAT=your_personal_access_token

# IA - Escolhe UMA das opções:

# Opção 1: Claude (Anthropic)
ANTHROPIC_API_KEY=your_anthropic_key

# Opção 2: OpenAI GPT-4
OPENAI_API_KEY=your_openai_key

# Opção 3: Ollama (local - não requer chave)
# Basta instalar Ollama: https://ollama.com/download
```

## 📝 Como Usar

### Configuração básica

Edita o ficheiro `main.py` com os teus dados:

```python
# Dados obrigatórios do PR
REPO = "MedicineOneAPI"
PR_ID = 14097

# Dados opcionais da issue (ou None)
ISSUE_KEY = "M1-28446"

# O que gerar
GENERATE_DOCUMENTATION = True
GENERATE_CODE_REVIEW = True
```

### Executar

```bash
python main.py
```

### Opções de configuração

#### 1. **Apenas PR (sem issue do Jira)**
```python
ISSUE_KEY = None
REPO = "MeuRepo"
PR_ID = 123
```

#### 2. **Apenas documentação**
```python
GENERATE_DOCUMENTATION = True
GENERATE_CODE_REVIEW = False
```

#### 3. **Apenas code review**
```python
GENERATE_DOCUMENTATION = False
GENERATE_CODE_REVIEW = True
```

#### 4. **Prompts personalizados**
```python
CUSTOM_CODE_REVIEW_PROMPT = """
Analisa o código com foco em:
- Segurança
- Performance
- Boas práticas
"""

CUSTOM_DOCUMENTATION_PROMPT = """
Gera documentação no formato OpenAPI/Swagger
"""
```

## 📂 Ficheiros Gerados

Após a execução, são criados os seguintes ficheiros:

| Ficheiro | Descrição |
|----------|-----------|
| `issue_data.json` | Dados da issue do Jira |
| `pr_commits.json` | Commits do Pull Request |
| `pr_files_content.json` | Ficheiros alterados no PR |
| `DOCUMENTATION.md` | 📝 Documentação técnica gerada por IA |
| `CODE_REVIEW.md` | 🔍 Code review detalhado |

## 🧩 Módulos

### `jira_client.py`
Cliente para integração com Jira API
- Busca issues
- Extrai summary e description

### `azdo_client.py`
Cliente para Azure DevOps API
- Busca Pull Requests
- Extrai commits e diff de ficheiros
- Obtém linhas adicionadas

### `ai_analyzer.py`
Analisador com IA (Claude, OpenAI ou Ollama)
- Gera documentação técnica
- Gera code reviews detalhados
- Suporta prompts personalizados

### `main.py`
Orquestrador principal
- Une todos os módulos
- Executa workflow completo
- Configuração centralizada

## 🔑 Como obter as API Keys

### Jira
1. Acede a [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Cria um novo token
3. Adiciona ao `.env`

### Azure DevOps
1. Acede ao teu Azure DevOps
2. User Settings → Personal Access Tokens
3. Cria um token com permissões de `Code (Read)`
4. Adiciona ao `.env`

### Claude (Anthropic)
1. Acede a [Anthropic Console](https://console.anthropic.com/)
2. Cria uma API key
3. Adiciona ao `.env`

### OpenAI
1. Acede a [OpenAI Platform](https://platform.openai.com/api-keys)
2. Cria uma API key
3. Adiciona ao `.env`

### Ollama (Local - Grátis)
1. Instala Ollama: [ollama.com/download](https://ollama.com/download)
2. Executa: `ollama pull llama3.2`
3. Inicia: `ollama serve`
4. Não requer configuração no `.env`

## 🛠️ Troubleshooting

### Erro: "Nenhum provedor de IA configurado"
- Verifica se tens uma das API keys configuradas no `.env`
- Ou instala e executa Ollama localmente

### Erro: "Autenticação falhou" (Jira)
- Confirma que o `JIRA_EMAIL` e `JIRA_API_TOKEN` estão corretos
- Verifica se o token tem permissões adequadas

### Erro: "Erro ao buscar PR" (Azure DevOps)
- Confirma que o `AZDO_PAT` tem permissões de leitura de código
- Verifica se o nome do repositório e PR ID estão corretos

### Erro: "TypeError: 'bool' object is not callable"
- Certifica-te de que estás a usar a versão atualizada do código
- Os métodos internos devem ser `_generate_documentation()` e `_generate_code_review()`

## 📄 Exemplos de Output

### Documentação Técnica
```markdown
## 📋 Resumo
Implementação de autenticação OAuth2...

## 🔧 Detalhes Técnicos
- Endpoint: POST /api/auth/login
- Parâmetros: email, password
...
```

### Code Review
```markdown
## 1. Resumo das Alterações
- Implementado sistema de cache Redis
- Melhorada performance em 40%

## 2. Análise de Qualidade
✅ Código bem estruturado
⚠️ Falta tratamento de erro em...

## 3. Sugestões
- Adicionar testes unitários para...
...
```

## 🤝 Contribuir

1. Fork o projeto
2. Cria uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit as mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abre um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT.

## 👥 Autores

Desenvolvido para automatizar análise de Pull Requests e documentação técnica.

---

**💡 Dica:** Para melhores resultados, usa prompts personalizados específicos para o teu contexto de projeto!
