import json
import requests
import time
import os

# ====================================================
# Script: get_repos.py
# Autor: Rafael Martins
# Descrição: Coleta dados de PRs de repositórios populares do GitHub.
# ====================================================

# ⚙️ Carrega o token do ambiente (evita expor segredo no código)
GITHUB_TOKEN = ''
START_INDEX = 11

if not GITHUB_TOKEN:
    raise EnvironmentError("❌ Variável de ambiente GITHUB_TOKEN não encontrada. Defina antes de executar.")

API_URL = "https://api.github.com/graphql"

# ====================================================
# Função: buscar os 200 repositórios mais populares
# ====================================================
def get_top_200_repos():
    query_template = """
    {
      search(query: "stars:>0 sort:stars-desc", type: REPOSITORY, first: 100, after: AFTER_CURSOR) {
        edges {
          node {
            ... on Repository {
              nameWithOwner
              stargazerCount
              url
            }
          }
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
    """

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    repos = []
    cursor = None
    has_next_page = True

    while has_next_page and len(repos) < 200:
        query = query_template.replace("AFTER_CURSOR", f'"{cursor}"' if cursor else "null")

        response = requests.post(API_URL, json={"query": query}, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Erro na requisição: {response.status_code} - {response.text}")

        data = response.json()
        search_data = data["data"]["search"]
        repos.extend(search_data["edges"])

        has_next_page = search_data["pageInfo"]["hasNextPage"]
        cursor = search_data["pageInfo"]["endCursor"]

        print(f"🔹 Repositórios coletados: {len(repos)}")
        time.sleep(1)  # respeita o limite de taxa da API

    return repos[:200]


# ====================================================
# Função: coletar até 100 PRs (MERGED ou CLOSED) de cada repositório
# ====================================================
def get_pull_requests_for_repos(repos, max_repos=200, max_prs_per_repo=100, repo_timeout=90):
    """
    Coleta PRs de repositórios com limite de tempo por repositório.
    - max_repos: máximo de repositórios a processar
    - max_prs_per_repo: máximo de PRs por repositório
    - repo_timeout: tempo máximo (segundos) para coletar PRs de um repositório
    """
    query_template = """
    {
      repository(owner: "OWNER", name: "NAME") {
        pullRequests(states: [MERGED, CLOSED], first: 20, after: AFTER_CURSOR, orderBy: {field: CREATED_AT, direction: DESC}) {
          edges {
            node {
              title
              url
              state
              createdAt
              closedAt
              mergedAt
              reviews { totalCount }
              files { totalCount }
              additions
              deletions
              body
              participants { totalCount }
              comments { totalCount }
            }
          }
          pageInfo {
            endCursor
            hasNextPage
          }
        }
      }
    }
    """

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    repo_pr_map = {}

    for index, repo in enumerate(repos[START_INDEX-1:], start=START_INDEX):
        repo_name_with_owner = repo['node']['nameWithOwner']
        owner, name = repo_name_with_owner.split('/')
        cursor = None
        has_next_page = True
        repo_pr_map[repo_name_with_owner] = []
        start_time = time.time()

        print(f"\n🚀 Coletando PRs de {repo_name_with_owner} ({index}/{min(len(repos), max_repos)})")

        while has_next_page and len(repo_pr_map[repo_name_with_owner]) < max_prs_per_repo:
            # ⏱️ Verifica se o tempo limite foi atingido
            if time.time() - start_time > repo_timeout:
                print(f"⏰ Tempo limite de {repo_timeout}s atingido para {repo_name_with_owner}. Pulando repositório.")
                break

            query = query_template.replace("OWNER", owner).replace("NAME", name).replace("AFTER_CURSOR", f'"{cursor}"' if cursor else "null")

            try:
                response = requests.post(API_URL, json={"query": query}, headers=headers, timeout=20)
            except requests.exceptions.Timeout:
                print(f"⚠️ Timeout na requisição do GitHub para {repo_name_with_owner}, pulando...")
                break
            except Exception as e:
                print(f"⚠️ Erro inesperado em {repo_name_with_owner}: {e}")
                break

            if response.status_code != 200:
                print(f"⚠️ Erro {response.status_code} em {repo_name_with_owner}, pulando...")
                break

            data = response.json()
            if "errors" in data:
                print(f"⚠️ Erros detectados em {repo_name_with_owner}: {data['errors']}")
                break

            pr_data = data["data"]["repository"]["pullRequests"]
            repo_pr_map[repo_name_with_owner].extend(pr_data["edges"])

            has_next_page = pr_data["pageInfo"]["hasNextPage"]
            cursor = pr_data["pageInfo"]["endCursor"]

            print(f"   → {len(repo_pr_map[repo_name_with_owner])} PRs coletados...")
            time.sleep(1)

        # Garante que o número máximo de PRs não seja excedido
        repo_pr_map[repo_name_with_owner] = repo_pr_map[repo_name_with_owner][:max_prs_per_repo]

        # 🔸 Salva progresso parcial a cada 10 repositórios
        if index % 10 == 0:
            partial_filename = f"repos_and_prs_partial_{index}.json"
            save_repos_and_prs_to_json(repos[:index], repo_pr_map, partial_filename)
            print(f"💾 Progresso salvo em {partial_filename}")

    return repo_pr_map



# ====================================================
# Função: salvar dados combinados em JSON
# ====================================================
def save_repos_and_prs_to_json(repos, repo_pr_map, json_filename):
    data = []

    for repo in repos:
        repo_name_with_owner = repo['node']['nameWithOwner']
        repo_stars = repo['node']['stargazerCount']
        repo_url = repo['node']['url']

        pull_requests = repo_pr_map.get(repo_name_with_owner, [])
        if not pull_requests:
            continue

        repo_data = {
            'repository': {
                'nameWithOwner': repo_name_with_owner,
                'stars': repo_stars,
                'url': repo_url,
                'pullRequests': []
            }
        }

        for pr in pull_requests:
          pr_node = pr.get('node', {})

          # ⚙️ Correção: usa ou {} caso o campo seja None
          files_info = pr_node.get('files') or {}
          participants_info = pr_node.get('participants') or {}
          comments_info = pr_node.get('comments') or {}
          reviews_info = pr_node.get('reviews') or {}

          pr_data = {
              'title': pr_node.get('title', ''),
              'url': pr_node.get('url', ''),
              'state': pr_node.get('state', ''),
              'createdAt': pr_node.get('createdAt', ''),
              'closedAt': pr_node.get('closedAt', ''),
              'mergedAt': pr_node.get('mergedAt', ''),
              'reviewCount': reviews_info.get('totalCount', 0),
              'numberOfFiles': files_info.get('totalCount', 0),
              'additions': pr_node.get('additions', 0),
              'deletions': pr_node.get('deletions', 0),
              'descriptionSize': len(pr_node.get('body', '') or ''),
              'participantsCount': participants_info.get('totalCount', 0),
              'commentsCount': comments_info.get('totalCount', 0)
          }

          repo_data['repository']['pullRequests'].append(pr_data)


        data.append(repo_data)

    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    print(f"\n💾 Dados salvos em {json_filename}")


# ====================================================
# Execução principal
# ====================================================
if __name__ == "__main__":
    print("🚀 Iniciando coleta de repositórios e PRs...")

    repos = get_top_200_repos()
    print(f"\n✅ Total de repositórios coletados: {len(repos)}")

    repo_pr_map = get_pull_requests_for_repos(repos)
    print(f"\n✅ Coleta de PRs concluída para {len(repo_pr_map)} repositórios.")

    save_repos_and_prs_to_json(repos, repo_pr_map, "repos_and_prs.json")

    print("\n🏁 Processo finalizado com sucesso!")
