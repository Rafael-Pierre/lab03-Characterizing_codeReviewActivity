import json
from datetime import datetime, timedelta
import os

def filter_pull_requests(input_filename, output_filename):
    print(f"🚀 Iniciando filtragem dos dados do arquivo: {input_filename}")

    # Verifica se o arquivo existe
    if not os.path.exists(input_filename):
        print(f"❌ ERRO: Arquivo '{input_filename}' não encontrado no diretório atual.")
        return

    # Carrega os dados JSON
    with open(input_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📦 Total de repositórios carregados: {len(data)}")

    filtered_data = []
    repos_names = []

    for repo in data:
        repo_name_with_owner = repo['repository']['nameWithOwner']
        prs = repo['repository'].get('pullRequests', [])
        print(f"🔍 Analisando {repo_name_with_owner} ({len(prs)} PRs)")

        filtered_pull_requests = []

        for pr in prs:
            created_at = datetime.fromisoformat(pr['createdAt'].replace("Z", "+00:00"))
            closed_at = datetime.fromisoformat(pr['closedAt'].replace("Z", "+00:00")) if pr['closedAt'] else None
            merged_at = datetime.fromisoformat(pr['mergedAt'].replace("Z", "+00:00")) if pr['mergedAt'] else None

            # Aceita PRs com revisão ou comentários
            has_reviews = (pr['reviewCount'] > 0) or (pr['commentsCount'] > 0)

            # Calcula o tempo de análise
            time_diff = None
            if merged_at:
                time_diff = merged_at - created_at
            elif closed_at:
                time_diff = closed_at - created_at

            # Aplica filtros
            if has_reviews and time_diff and time_diff >= timedelta(minutes=10):
                filtered_pull_requests.append(pr)

        print(f"   ✅ {len(filtered_pull_requests)} PRs válidos após filtragem")

        # Mantém repositórios com pelo menos 20 PRs válidos
        if len(filtered_pull_requests) >= 20:
            filtered_repo_data = {
                'repository': {
                    'nameWithOwner': repo_name_with_owner,
                    'stars': repo['repository']['stars'],
                    'url': repo['repository']['url'],
                    'pullRequests': filtered_pull_requests
                }
            }
            filtered_data.append(filtered_repo_data)
            repos_names.append(repo_name_with_owner)

    # Salva os arquivos resultantes
    if filtered_data:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4)
        with open('repos_names.json', 'w', encoding='utf-8') as f:
            json.dump(repos_names, f, indent=4)
        print(f"\n💾 {len(filtered_data)} repositórios válidos salvos em '{output_filename}'")
    else:
        print("\n⚠️ Nenhum repositório atendeu aos critérios definidos — verifique os filtros ou os dados de entrada.")

if __name__ == "__main__":
    filter_pull_requests("repos_and_prs.json", "filtered_prs.json")
