import json
import os
from datetime import datetime

class DataFormatter:
    """Formata dados do Jira e Azure DevOps para um formato legível para IA"""

    def __init__(self):
        self.issue_data = None
        self.pr_data = None
        self.pr_commits = None
        self.pr_files = None
        self.pr_files_content = None

    def load_json_file(self, filename):
        """Carrega um ficheiro JSON"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"[AVISO] Ficheiro {filename} nao encontrado")
                return None
        except Exception as e:
            print(f"[ERRO] Erro ao ler {filename}: {e}")
            return None

    def load_all_data(self):
        """Carrega todos os ficheiros JSON"""
        print("Carregando dados...")
        self.issue_data = self.load_json_file('issue_data.json')
        self.pr_data = self.load_json_file('pr_data.json')
        self.pr_commits = self.load_json_file('pr_commits.json')
        self.pr_files = self.load_json_file('pr_files.json')
        self.pr_files_content = self.load_json_file('pr_files_content.json')
        print("Dados carregados com sucesso!")

    def format_jira_issue(self):
        """Formata dados da issue do Jira"""
        if not self.issue_data:
            return None

        fields = self.issue_data.get('fields', {})

        # Extrair descrição (pode estar em formato ADF - Atlassian Document Format)
        description = fields.get('description', '')
        if isinstance(description, dict):
            # Se for ADF, tentar extrair texto
            description = self._extract_text_from_adf(description)

        return {
            'issue_key': self.issue_data.get('key'),
            'summary': fields.get('summary', ''),
            'description': description,
            'type': fields.get('issuetype', {}).get('name', ''),
            'status': fields.get('status', {}).get('name', ''),
            'priority': fields.get('priority', {}).get('name', ''),
            'assignee': fields.get('assignee', {}).get('displayName', 'N/A'),
            'reporter': fields.get('reporter', {}).get('displayName', 'N/A'),
            'created': fields.get('created', ''),
            'updated': fields.get('updated', '')
        }

    def _extract_text_from_adf(self, adf_doc):
        """Extrai texto de um documento ADF (Atlassian Document Format)"""
        if not isinstance(adf_doc, dict):
            return str(adf_doc)

        text_parts = []

        def extract_content(node):
            if isinstance(node, dict):
                # Se tem texto, adiciona
                if 'text' in node:
                    text_parts.append(node['text'])

                # Processar conteúdo interno
                if 'content' in node:
                    for child in node['content']:
                        extract_content(child)

            elif isinstance(node, list):
                for item in node:
                    extract_content(item)

        extract_content(adf_doc)
        return '\n'.join(text_parts)

    def format_pr_data(self):
        """Formata dados do Pull Request"""
        if not self.pr_data:
            return None

        return {
            'pr_id': self.pr_data.get('pullRequestId'),
            'title': self.pr_data.get('title'),
            'description': self.pr_data.get('description', ''),
            'status': self.pr_data.get('status'),
            'source_branch': self.pr_data.get('sourceRefName', '').replace('refs/heads/', ''),
            'target_branch': self.pr_data.get('targetRefName', '').replace('refs/heads/', ''),
            'created_by': self.pr_data.get('createdBy', {}).get('displayName', 'N/A'),
            'creation_date': self.pr_data.get('creationDate', ''),
            'url': self.pr_data.get('url', '')
        }

    def format_commits(self):
        """Formata lista de commits"""
        if not self.pr_commits:
            return []

        commits = []
        for commit in self.pr_commits.get('value', []):
            commits.append({
                'commit_id': commit.get('commitId', '')[:8],
                'message': commit.get('comment', ''),
                'author': commit.get('author', {}).get('name', 'N/A'),
                'date': commit.get('author', {}).get('date', '')
            })

        return commits

    def format_file_changes(self):
        """Formata alterações de ficheiros"""
        if not self.pr_files:
            return []

        changes = []
        for file_info in self.pr_files.get('files', []):
            changes.append({
                'path': file_info['path'],
                'change_type': file_info['changeType']
            })

        return changes

    def format_file_contents(self):
        """Formata conteúdo dos ficheiros com alterações"""
        if not self.pr_files_content:
            return []

        files = []
        for file_info in self.pr_files_content.get('files', []):
            content_before = file_info.get('content_before', '')
            content_after = file_info.get('content_after', '')

            # Calcular estatísticas
            lines_before = len(content_before.split('\n')) if content_before else 0
            lines_after = len(content_after.split('\n')) if content_after else 0
            lines_added = lines_after - lines_before if file_info['changeType'] != 'delete' else 0
            lines_removed = lines_before - lines_after if file_info['changeType'] != 'add' else 0

            files.append({
                'path': file_info['path'],
                'change_type': file_info['changeType'],
                'lines_before': lines_before,
                'lines_after': lines_after,
                'lines_changed': abs(lines_added - lines_removed),
                'content_before': content_before,
                'content_after': content_after
            })

        return files

    def generate_formatted_output(self):
        """Gera output formatado com todos os dados"""
        self.load_all_data()

        formatted_data = {
            'jira_issue': self.format_jira_issue(),
            'pull_request': self.format_pr_data(),
            'commits': self.format_commits(),
            'file_changes_summary': self.format_file_changes(),
            'file_contents': self.format_file_contents(),
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_commits': len(self.format_commits()),
                'total_files_changed': len(self.format_file_changes())
            }
        }

        return formatted_data

    def save_formatted_output(self, output_file='formatted_data.json'):
        """Salva output formatado em ficheiro"""
        formatted_data = self.generate_formatted_output()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, indent=4, ensure_ascii=False)

        print(f"\nDados formatados salvos em {output_file}")
        return formatted_data

    def generate_readable_summary(self, formatted_data):
        """Gera um resumo legível em texto"""
        summary = []

        # Jira Issue
        if formatted_data.get('jira_issue'):
            issue = formatted_data['jira_issue']
            summary.append("="*80)
            summary.append("JIRA ISSUE")
            summary.append("="*80)
            summary.append(f"Key: {issue['issue_key']}")
            summary.append(f"Tipo: {issue['type']} | Status: {issue['status']} | Prioridade: {issue['priority']}")
            summary.append(f"\nSumario: {issue['summary']}")
            summary.append(f"\nDescricao:\n{issue['description']}")
            summary.append(f"\nAssignee: {issue['assignee']} | Reporter: {issue['reporter']}")
            summary.append("")

        # Pull Request
        if formatted_data.get('pull_request'):
            pr = formatted_data['pull_request']
            summary.append("="*80)
            summary.append("PULL REQUEST")
            summary.append("="*80)
            summary.append(f"ID: #{pr['pr_id']}")
            summary.append(f"Titulo: {pr['title']}")
            summary.append(f"Status: {pr['status']}")
            summary.append(f"Branch: {pr['source_branch']} -> {pr['target_branch']}")
            summary.append(f"Criado por: {pr['created_by']} em {pr['creation_date']}")
            if pr['description']:
                summary.append(f"\nDescricao: {pr['description']}")
            summary.append("")

        # Commits
        if formatted_data.get('commits'):
            summary.append("="*80)
            summary.append(f"COMMITS ({len(formatted_data['commits'])})")
            summary.append("="*80)
            for commit in formatted_data['commits']:
                summary.append(f"  [{commit['commit_id']}] {commit['message']}")
                summary.append(f"      Por: {commit['author']} em {commit['date']}")
            summary.append("")

        # Ficheiros alterados
        if formatted_data.get('file_changes_summary'):
            summary.append("="*80)
            summary.append(f"FICHEIROS ALTERADOS ({len(formatted_data['file_changes_summary'])})")
            summary.append("="*80)
            for file_change in formatted_data['file_changes_summary']:
                summary.append(f"  [{file_change['change_type']}] {file_change['path']}")
            summary.append("")

        # Estatísticas de alterações
        if formatted_data.get('file_contents'):
            summary.append("="*80)
            summary.append("ESTATISTICAS DE CODIGO")
            summary.append("="*80)
            for file_content in formatted_data['file_contents']:
                summary.append(f"\n{file_content['path']}")
                summary.append(f"  Tipo: {file_content['change_type']}")
                if file_content['change_type'] == 'add':
                    summary.append(f"  Ficheiro novo: {file_content['lines_after']} linhas")
                elif file_content['change_type'] == 'delete':
                    summary.append(f"  Ficheiro apagado: tinha {file_content['lines_before']} linhas")
                else:
                    summary.append(f"  Antes: {file_content['lines_before']} linhas")
                    summary.append(f"  Depois: {file_content['lines_after']} linhas")
                    summary.append(f"  Alteracao: {file_content['lines_changed']} linhas")

        return '\n'.join(summary)


if __name__ == "__main__":
    formatter = DataFormatter()

    print("Formatando dados do Jira e Azure DevOps...\n")

    # Gerar e salvar dados formatados
    formatted_data = formatter.save_formatted_output()

    # Gerar e mostrar resumo legível
    summary = formatter.generate_readable_summary(formatted_data)

    # Salvar resumo em ficheiro de texto
    with open('readable_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)

    print("\nResumo legivel salvo em readable_summary.txt")
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(summary)