# ==============================================================
# Script: analyze_prs.py
# Autor: Rafael Martins
# Descrição: Análise de Pull Requests (PRs) coletados do GitHub
# Sprint 3 - Laboratório de Experimentação de Software
# ==============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr

# --------------------------------------------------------------
# 1️⃣ Leitura do dataset
# --------------------------------------------------------------
print("📂 Lendo dataset 'filtered_prs.json'...")

# Carrega o arquivo JSON e normaliza estrutura aninhada
import json
with open("filtered_prs.json", "r", encoding="utf-8") as f:
    data = json.load(f)
df = pd.json_normalize(data, record_path=["repository", "pullRequests"], meta=[["repository", "nameWithOwner"]])

print(f"✅ Total de registros (PRs): {len(df)}")

# --------------------------------------------------------------
# 2️⃣ Pré-processamento e criação de métricas auxiliares
# --------------------------------------------------------------
print("🧩 Processando métricas...")

# Converte datas
df["createdAt"] = pd.to_datetime(df["createdAt"], errors="coerce")
df["closedAt"] = pd.to_datetime(df["closedAt"], errors="coerce")
df["mergedAt"] = pd.to_datetime(df["mergedAt"], errors="coerce")

# Calcula data final (merge ou close)
df["finalDate"] = df["mergedAt"].fillna(df["closedAt"])

# Tempo de análise em horas
df["analysis_time_hours"] = (df["finalDate"] - df["createdAt"]).dt.total_seconds() / 3600

# Tamanho total (adições + deleções)
df["total_changes"] = df["additions"] + df["deletions"]

# Interações totais (comentários + participantes)
df["interactions"] = df["commentsCount"] + df["participantsCount"]

# Filtra PRs válidos
df = df.dropna(subset=["analysis_time_hours"])

print("✅ Métricas calculadas com sucesso!")

# --------------------------------------------------------------
# 3️⃣ Cálculo das correlações (Spearman)
# --------------------------------------------------------------
print("\n📈 Calculando correlações (Spearman)...")

def calc_corr(x, y):
    corr, _ = spearmanr(df[x], df[y])
    return round(corr, 3)

correlacoes = {
    "RQ01": calc_corr("total_changes", "state"),  # não numérico, apenas ilustrativo
    "RQ02": calc_corr("analysis_time_hours", "reviewCount"),
    "RQ03": calc_corr("descriptionSize", "reviewCount"),
    "RQ04": calc_corr("interactions", "reviewCount"),
    "RQ05": calc_corr("total_changes", "reviewCount"),
    "RQ06": calc_corr("analysis_time_hours", "reviewCount"),
    "RQ07": calc_corr("descriptionSize", "reviewCount"),
    "RQ08": calc_corr("interactions", "reviewCount"),
}

print("✅ Correlações calculadas com sucesso!")
print("\n📊 Resultados das correlações (Spearman):")
for rq, corr in correlacoes.items():
    print(f"{rq}: {corr}")

# --------------------------------------------------------------
# 4️⃣ Geração dos gráficos (um para cada RQ)
# --------------------------------------------------------------
print("\n🎨 Gerando gráficos...")

sns.set(style="whitegrid")
plt.rcParams["axes.titlesize"] = 13

# --- RQ01: Tamanho x Status ---
plt.figure(figsize=(8,5))
sns.boxplot(x="state", y="total_changes", data=df)
plt.title("RQ01 - Tamanho dos PRs vs Status Final")
plt.xlabel("Status do PR")
plt.ylabel("Linhas adicionadas + removidas")
plt.tight_layout()
plt.savefig("grafico_RQ01.png")
plt.close()

# --- RQ02: Tempo x Status ---
plt.figure(figsize=(8,5))
sns.boxplot(x="state", y="analysis_time_hours", data=df)
plt.title("RQ02 - Tempo de Análise vs Status Final")
plt.xlabel("Status do PR")
plt.ylabel("Tempo de Análise (horas)")
plt.tight_layout()
plt.savefig("grafico_RQ02.png")
plt.close()

# --- RQ03: Descrição x Status ---
plt.figure(figsize=(8,5))
sns.boxplot(x="state", y="descriptionSize", data=df)
plt.title("RQ03 - Descrição vs Status Final")
plt.xlabel("Status do PR")
plt.ylabel("Tamanho da Descrição (caracteres)")
plt.tight_layout()
plt.savefig("grafico_RQ03.png")
plt.close()

# --- RQ04: Interações x Status ---
plt.figure(figsize=(8,5))
sns.boxplot(x="state", y="interactions", data=df)
plt.title("RQ04 - Interações vs Status Final")
plt.xlabel("Status do PR")
plt.ylabel("Total de Interações")
plt.tight_layout()
plt.savefig("grafico_RQ04.png")
plt.close()

# --- RQ05: Tamanho x Revisões ---
plt.figure(figsize=(6,5))
sns.scatterplot(x="total_changes", y="reviewCount", data=df)
plt.title("RQ05 - Tamanho vs Revisões")
plt.xlabel("Linhas adicionadas + removidas")
plt.ylabel("Número de Revisões")
plt.tight_layout()
plt.savefig("grafico_RQ05.png")
plt.close()

# --- RQ06: Tempo x Revisões ---
plt.figure(figsize=(6,5))
sns.scatterplot(x="analysis_time_hours", y="reviewCount", data=df)
plt.title("RQ06 - Tempo de Análise vs Revisões")
plt.xlabel("Tempo de Análise (horas)")
plt.ylabel("Número de Revisões")
plt.tight_layout()
plt.savefig("grafico_RQ06.png")
plt.close()

# --- RQ07: Descrição x Revisões ---
plt.figure(figsize=(6,5))
sns.scatterplot(x="descriptionSize", y="reviewCount", data=df)
plt.title("RQ07 - Descrição vs Revisões")
plt.xlabel("Tamanho da Descrição (caracteres)")
plt.ylabel("Número de Revisões")
plt.tight_layout()
plt.savefig("grafico_RQ07.png")
plt.close()

# --- RQ08: Interações x Revisões ---
plt.figure(figsize=(6,5))
sns.scatterplot(x="interactions", y="reviewCount", data=df)
plt.title("RQ08 - Interações vs Revisões")
plt.xlabel("Total de Interações")
plt.ylabel("Número de Revisões")
plt.tight_layout()
plt.savefig("grafico_RQ08.png")
plt.close()

print("✅ Gráficos salvos com sucesso (grafico_RQ01.png → grafico_RQ08.png)")

# --------------------------------------------------------------
# 5️⃣ Estatísticas descritivas (tabelas resumo)
# --------------------------------------------------------------
print("\n📋 Estatísticas descritivas das principais métricas:\n")
print(df[["total_changes", "analysis_time_hours", "descriptionSize", "interactions", "reviewCount"]].describe())

print("\n🏁 Análise concluída! Os gráficos e resultados estão prontos para o relatório final.")
