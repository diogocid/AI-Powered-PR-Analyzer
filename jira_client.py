import requests
from requests.auth import HTTPBasicAuth
import json
import os
from dotenv import load_dotenv

class JiraClient:
    def __init__(self):
        load_dotenv()
        self.jira_url = os.getenv('JIRA_URL')
        self.email = os.getenv('JIRA_EMAIL')
        self.api_token = os.getenv('JIRA_API_TOKEN')
        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {"Accept": "application/json"}

    def test_connection(self):
        """Testa a conexão e autenticação com o Jira"""
        url = f"{self.jira_url}/rest/api/3/myself"

        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)

            if response.status_code == 200:
                user_data = response.json()
                print(f"[OK] Autenticacao bem sucedida!")
                print(f"  User: {user_data.get('displayName')}")
                print(f"  Email: {user_data.get('emailAddress')}")
                return True
            else:
                print(f"[ERRO] Autenticacao falhou - Status {response.status_code}")
                print(f"  Mensagem: {response.text}")
                return False
        except Exception as e:
            print(f"[ERRO] Erro ao conectar: {e}")
            return False

    def get_issue(self, issue_key):
        """Busca uma issue do Jira pelo key"""
        url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"

        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Erro ao conectar ao Jira: {e}")
            return None

    def get_issue_summary_only(self, issue_key):
        """Busca apenas summary e description da issue"""
        url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"

        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)

            if response.status_code == 200:
                data = response.json()
                fields = data.get('fields', {})

                return {
                    'key': data.get('key'),
                    'summary': fields.get('summary'),
                    'description': fields.get('description')
                }
            else:
                print(f"Erro {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Erro ao conectar ao Jira: {e}")
            return None

    def print_issue_summary(self, issue_data):
        """Imprime um resumo formatado da issue"""
        if not issue_data:
            return

        fields = issue_data.get('fields', {})

        print("\n" + "="*80)
        print(f"Issue: {issue_data.get('key')}")
        print("="*80)
        print(f"Tipo: {fields.get('issuetype', {}).get('name', 'N/A')}")
        print(f"Status: {fields.get('status', {}).get('name', 'N/A')}")
        print(f"Prioridade: {fields.get('priority', {}).get('name', 'N/A')}")
        print(f"Sumário: {fields.get('summary', 'N/A')}")
        print(f"\nDescrição:")
        print(f"{fields.get('description', 'N/A')}")
        print(f"\nCriado: {fields.get('created', 'N/A')}")
        print(f"Atualizado: {fields.get('updated', 'N/A')}") 

        if fields.get('assignee'):
            print(f"Assignee: {fields['assignee'].get('displayName', 'N/A')}")

        if fields.get('reporter'):
            print(f"Reporter: {fields['reporter'].get('displayName', 'N/A')}")

        print("="*80 + "\n")


if __name__ == "__main__":
    client = JiraClient()

    issue_key = "PROJ-123"
    print(f"Buscando issue {issue_key}...\n")

    issue_data = client.get_issue_summary_only(issue_key)

    if issue_data:
        print(f"Key: {issue_data['key']}")
        print(f"Summary: {issue_data['summary']}\n")

        with open('issue_data.json', 'w', encoding='utf-8') as f:
            json.dump(issue_data, f, indent=4, ensure_ascii=False)
        print("✓ issue_data.json criado")