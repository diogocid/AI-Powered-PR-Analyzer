import requests
from requests.auth import HTTPBasicAuth
import json
import os
from dotenv import load_dotenv
import urllib.parse
import difflib

class AzureDevOpsClient:
    def __init__(self):
        load_dotenv()
        self.organization = os.getenv('AZDO_ORGANIZATION')
        self.project = os.getenv('AZDO_PROJECT')
        self.pat = os.getenv('AZDO_PAT')
        self.auth = HTTPBasicAuth("", self.pat)
        self.headers = {"Accept": "application/json"}
        self.base_url = f"https://dev.azure.com/{self.organization}"

    def get_pull_request(self, repo, pr_id):
        """Busca um Pull Request do Azure DevOps"""
        project_encoded = urllib.parse.quote(self.project)
        url = f"{self.base_url}/{project_encoded}/_apis/git/repositories/{repo}/pullrequests/{pr_id}?api-version=7.0"

        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Erro ao buscar PR: {e}")
            return None

    def get_pr_commits(self, repo, pr_id):
        """Busca os commits de um Pull Request"""
        project_encoded = urllib.parse.quote(self.project)
        url = f"{self.base_url}/{project_encoded}/_apis/git/repositories/{repo}/pullrequests/{pr_id}/commits?api-version=7.0"

        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro ao buscar commits {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Erro ao buscar commits: {e}")
            return None

    def get_pr_diff(self, repo, pr_id):
        """Busca o diff completo do Pull Request"""
        pr_data = self.get_pull_request(repo, pr_id)
        if not pr_data:
            return None

        source_branch = pr_data.get('sourceRefName', '').replace('refs/heads/', '')
        target_branch = pr_data.get('targetRefName', '').replace('refs/heads/', '')

        if not source_branch or not target_branch:
            print("Não foi possível obter as branches do PR")
            return None

        project_encoded = urllib.parse.quote(self.project)
        url = f"{self.base_url}/{project_encoded}/_apis/git/repositories/{repo}/diffs/commits?baseVersion={target_branch}&targetVersion={source_branch}&$top=1000&api-version=7.0"

        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro ao buscar diff do PR {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Erro ao buscar diff do PR: {e}")
            return None

    def get_file_content(self, repo, file_path, version_descriptor):
        """Busca o conteúdo de um ficheiro numa versão específica"""
        project_encoded = urllib.parse.quote(self.project)
        url = f"{self.base_url}/{project_encoded}/_apis/git/repositories/{repo}/blobs/{version_descriptor}?$format=text&api-version=7.0"

        try:
            headers = {"Accept": "text/plain"}
            response = requests.get(url, headers=headers, auth=self.auth)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Erro ao buscar blob {version_descriptor}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro ao buscar conteúdo de {file_path}: {e}")
            return None

    def get_pr_added_lines_only(self, repo, pr_id):
        """Busca apenas as linhas adicionadas nos ficheiros do PR"""
        pr_data = self.get_pull_request(repo, pr_id)
        if not pr_data:
            return None

        diff_data = self.get_pr_diff(repo, pr_id)
        if not diff_data:
            return None

        source_branch = pr_data.get('sourceRefName', '').replace('refs/heads/', '')
        target_branch = pr_data.get('targetRefName', '').replace('refs/heads/', '')

        files_with_additions = []

        for change in diff_data.get('changes', []):
            item = change.get('item', {})

            if item.get('isFolder', False):
                continue

            file_path = item.get('path')
            change_type = change.get('changeType')

            file_info = {
                'path': file_path,
                'changeType': change_type,
                'added_lines': []
            }

            if change_type == 'add':
                object_id = item.get('objectId')
                if object_id:
                    content = self.get_file_content(repo, file_path, object_id)
                    if content:
                        file_info['added_lines'] = content.splitlines()

            elif change_type == 'edit':
                original_object_id = item.get('originalObjectId')
                object_id = item.get('objectId')

                if original_object_id and object_id:
                    content_before = self.get_file_content(repo, file_path, original_object_id)
                    content_after = self.get_file_content(repo, file_path, object_id)

                    if content_before and content_after:
                        lines_before = content_before.splitlines()
                        lines_after = content_after.splitlines()

                        differ = difflib.Differ()
                        diff = list(differ.compare(lines_before, lines_after))

                        added_lines = [line[2:] for line in diff if line.startswith('+ ')]
                        file_info['added_lines'] = added_lines

            if file_info['added_lines']:
                files_with_additions.append(file_info)

        return {
            'files': files_with_additions,
            'total': len(files_with_additions),
            'source_branch': source_branch,
            'target_branch': target_branch
        }


if __name__ == "__main__":
    client = AzureDevOpsClient()

    repo = "MyRepository"
    pr_id = 12345
    print(f"Buscando Pull Request #{pr_id} do repositorio {repo}...\n")

    # Gerar pr_commits.json
    print("Buscando commits do PR...")
    commits_data = client.get_pr_commits(repo, pr_id)
    if commits_data:
        commits_list = commits_data.get('value', [])
        print(f"Total de commits: {len(commits_list)}")

        with open('pr_commits.json', 'w', encoding='utf-8') as f:
            json.dump(commits_data, f, indent=4, ensure_ascii=False)
        print("✓ pr_commits.json criado\n")

    # Gerar pr_files_content.json
    print("Buscando linhas adicionadas nos ficheiros do PR...")
    added_lines_data = client.get_pr_added_lines_only(repo, pr_id)
    if added_lines_data:
        print(f"Total de ficheiros com linhas adicionadas: {added_lines_data['total']}")

        with open('pr_files_content.json', 'w', encoding='utf-8') as f:
            json.dump(added_lines_data, f, indent=4, ensure_ascii=False)
        print("✓ pr_files_content.json criado\n")

        # Mostrar resumo
        print("Resumo das linhas adicionadas:")
        for file_info in added_lines_data.get('files', []):
            print(f"  • {file_info['path']}: {len(file_info['added_lines'])} linhas adicionadas")
