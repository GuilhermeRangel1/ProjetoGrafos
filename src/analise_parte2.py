"""
Parte 2 – Dataset Spotify (Kaggle) – Comparação de Algoritmos
Nós   : faixas musicais (track_id)
Arestas: K vizinhos mais próximos com base em distância euclidiana
         sobre features de áudio normalizadas (min-max).
Peso   : distância euclidiana normalizada (>= 0).
Para Bellman-Ford com pesos negativos usa-se um subgrafo com
offset = -media_distancia, tornando arestas "acima da média" negativas.
"""

import pandas as pd
import os
import sys
import json
import time
import random
import math

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from graphs.graph import Grafo
from graphs.algorithms import bfs, dfs, dijkstra, bellman_ford

# ---------------------------------------------------------------------------
BASE     = os.path.dirname(os.path.dirname(__file__))
DATASET  = os.path.join(BASE, "data", "dataset_parte2", "dataset.csv")
OUT      = os.path.join(BASE, "out")

FEATURES = ["danceability", "energy", "loudness", "speechiness",
            "acousticness", "instrumentalness", "liveness", "valence", "tempo"]

N_SAMPLE    = 2000   # nós do grafo principal
K_NEIGHBORS = 30     # arestas por nó  →  ≈ 60 k arestas direcionadas
N_BF        = 300    # subgrafo menor para Bellman-Ford (evita timeout)
K_BF        = 15
random.seed(42)
np.random.seed(42)
# ---------------------------------------------------------------------------


# ── helpers ─────────────────────────────────────────────────────────────────

def normalizar(df):
    X = df[FEATURES].astype(float).copy()
    for col in FEATURES:
        mn, mx = X[col].min(), X[col].max()
        X[col] = (X[col] - mn) / (mx - mn) if mx > mn else 0.0
    return X


def dist_matrix(X_np):
    """Pairwise euclidean distance matrix via algebra (numpy, não é algoritmo de grafo)."""
    sq   = np.sum(X_np ** 2, axis=1)
    D_sq = sq[:, None] + sq[None, :] - 2.0 * (X_np @ X_np.T)
    return np.sqrt(np.maximum(D_sq, 0.0))


def construir_grafo_knn(nos, D, K, offset=0.0):
    """Cria grafo dirigido KNN a partir da matriz de distâncias."""
    n = len(nos)
    g = Grafo(dirigido=True)
    for no in nos:
        g.adicionar_no(no)

    np.fill_diagonal(D, np.inf)
    knn_idx = np.argpartition(D, K, axis=1)[:, :K]

    for i in range(n):
        for j in knn_idx[i]:
            peso = round(float(D[i, j]) + offset, 5)
            g.adicionar_aresta(nos[i], nos[j], peso)

    np.fill_diagonal(D, 0.0)
    return g


def construir_dag_negativo(nos_bf, D_bf, K=8):
    """DAG onde arestas só vão de índice menor para maior (sem ciclos possíveis).
    Alguns pesos são negativos (offset = -media_dist/2), mas sem ciclo negativo."""
    n = len(nos_bf)
    media = float(np.mean(D_bf[D_bf > 0]))
    offset = -(media / 2.0)

    g = Grafo(dirigido=True)
    for no in nos_bf:
        g.adicionar_no(no)

    np.fill_diagonal(D_bf, np.inf)
    for i in range(n):
        knn = np.argpartition(D_bf[i], min(K, n - 1))[:K]
        for j in knn:
            if j > i:  # só arestas i→j com j>i → DAG garantido
                peso = round(float(D_bf[i, j]) + offset, 5)
                g.adicionar_aresta(nos_bf[i], nos_bf[j], peso)
    np.fill_diagonal(D_bf, 0.0)
    return g


def grafo_com_ciclo_negativo(base_nos, base_D):
    """Subgrafo com 3 arestas artificiais formando ciclo negativo."""
    g = Grafo(dirigido=True)
    a, b, c = base_nos[0], base_nos[1], base_nos[2]
    # arestas reais positivas para conectar o resto do subgrafo
    n = min(10, len(base_nos))
    for i in range(n):
        for j in range(n):
            if i != j and float(base_D[i, j]) < 0.5:
                g.adicionar_aresta(base_nos[i], base_nos[j],
                                   round(float(base_D[i, j]), 5))
    # ciclo artificial a→b→c→a com peso total = -3
    g.adicionar_aresta(a, b, -1.0)
    g.adicionar_aresta(b, c, -1.0)
    g.adicionar_aresta(c, a, -1.0)
    return g, a, b


def caminho_str(caminho, mapa_nome):
    return " → ".join(mapa_nome.get(n, n) for n in caminho)


# ── carregamento e amostragem ────────────────────────────────────────────────

def carregar_dataset():
    print("Carregando dataset…")
    df = pd.read_csv(DATASET)
    df = df.dropna(subset=FEATURES + ["track_id", "track_name", "track_genre"])
    df = df.drop_duplicates(subset="track_id")
    return df


def amostrar(df, n):
    """Amostra estratificada por gênero para maior diversidade."""
    generos = df["track_genre"].unique()
    por_genero = max(1, n // len(generos))
    partes = []
    for g in generos:
        sub = df[df["track_genre"] == g]
        partes.append(sub.sample(min(por_genero, len(sub)), random_state=42))
    sample = pd.concat(partes).drop_duplicates("track_id")
    if len(sample) > n:
        sample = sample.sample(n, random_state=42)
    return sample.reset_index(drop=True)


# ── execuções dos algoritmos ─────────────────────────────────────────────────

def rodar_bfs(grafo, fontes, mapa_nome):
    resultados = []
    for origem in fontes:
        t0 = time.perf_counter()
        ordem, niveis, _ = bfs(grafo, origem)
        t1 = time.perf_counter()
        max_camada = max(niveis.values()) if niveis else 0
        resultados.append({
            "origem"       : mapa_nome.get(origem, origem),
            "nos_visitados": len(ordem),
            "camadas"      : max_camada,
            "tempo_s"      : round(t1 - t0, 5),
        })
        print(f"  BFS de '{mapa_nome.get(origem,origem)}': "
              f"{len(ordem)} nós | {max_camada} camadas | {t1-t0:.4f}s")
    return resultados


def rodar_dfs(grafo, fontes, mapa_nome):
    resultados = []
    for origem in fontes:
        t0 = time.perf_counter()
        ordem, ciclo, arestas_cls = dfs(grafo, origem)
        t1 = time.perf_counter()
        contagem = {}
        for tipo in arestas_cls.values():
            contagem[tipo] = contagem.get(tipo, 0) + 1
        resultados.append({
            "origem"          : mapa_nome.get(origem, origem),
            "nos_visitados"   : len(ordem),
            "tem_ciclo"       : ciclo,
            "arestas_tree"    : contagem.get("tree", 0),
            "arestas_back"    : contagem.get("back", 0),
            "arestas_forward" : contagem.get("forward", 0),
            "arestas_cross"   : contagem.get("cross", 0),
            "tempo_s"         : round(t1 - t0, 5),
        })
        print(f"  DFS de '{mapa_nome.get(origem,origem)}': "
              f"ciclo={ciclo} | {len(ordem)} nós | {t1-t0:.4f}s")
    return resultados


def rodar_dijkstra(grafo, pares, mapa_nome):
    resultados = []
    for origem, destino in pares:
        t0 = time.perf_counter()
        custo, caminho = dijkstra(grafo, origem, destino)
        t1 = time.perf_counter()
        resultados.append({
            "origem"  : mapa_nome.get(origem, origem),
            "destino" : mapa_nome.get(destino, destino),
            "custo"   : round(custo, 5) if custo != float("inf") else "inalcancavel",
            "caminho" : caminho_str(caminho, mapa_nome),
            "saltos"  : len(caminho) - 1 if caminho else 0,
            "tempo_s" : round(t1 - t0, 5),
        })
        print(f"  Dijkstra {mapa_nome.get(origem,origem)[:20]} -> "
              f"{mapa_nome.get(destino,destino)[:20]}: "
              f"custo={round(custo,4)} | {t1-t0:.4f}s")
    return resultados


def rodar_bellman_ford(grafo, pares, mapa_nome, tag=""):
    resultados = []
    for origem, destino in pares:
        t0 = time.perf_counter()
        distancias, caminho, ciclo_neg = bellman_ford(grafo, origem, destino)
        t1 = time.perf_counter()
        custo = distancias.get(destino, float("inf"))
        resultados.append({
            "tag"                    : tag,
            "origem"                 : mapa_nome.get(origem, origem),
            "destino"                : mapa_nome.get(destino, destino),
            "custo"                  : round(custo, 5) if custo != float("inf") else "inalcancavel",
            "caminho"                : caminho_str(caminho, mapa_nome),
            "ciclo_negativo_detectado": ciclo_neg,
            "tempo_s"                : round(t1 - t0, 5),
        })
        nome_o = mapa_nome.get(origem, origem)[:20].encode("ascii", "replace").decode()
        nome_d = mapa_nome.get(destino, destino)[:20].encode("ascii", "replace").decode()
        print(f"  BF[{tag}] {nome_o} -> {nome_d}: "
              f"custo={round(custo,5)} ciclo={ciclo_neg} | {t1-t0:.4f}s")
    return resultados


# ── visualizações ────────────────────────────────────────────────────────────

def vis_distribuicao_graus(grafo, nos, titulo, arquivo):
    graus = [len(grafo.obter_vizinhos_simples(n)) for n in nos]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(graus, bins=30, color="#1DB954", edgecolor="black", linewidth=0.5)
    ax.set_title(titulo, fontsize=14, fontweight="bold")
    ax.set_xlabel("Grau de saída (k)", fontsize=12)
    ax.set_ylabel("Número de nós", fontsize=12)
    ax.axvline(sum(graus)/len(graus), color="red", linestyle="--",
               label=f"Média = {sum(graus)/len(graus):.1f}")
    ax.legend()
    plt.tight_layout()
    plt.savefig(arquivo, dpi=120)
    plt.close()
    print(f"  Salvo: {arquivo}")


def vis_tempo_algoritmos(report, arquivo):
    algs   = ["BFS", "DFS", "Dijkstra", "Bellman-Ford\n(sem ciclo neg.)", "Bellman-Ford\n(ciclo neg.)"]
    tempos = [
        sum(r["tempo_s"] for r in report["bfs"]) / len(report["bfs"]),
        sum(r["tempo_s"] for r in report["dfs"]) / len(report["dfs"]),
        sum(r["tempo_s"] for r in report["dijkstra"]) / len(report["dijkstra"]),
        sum(r["tempo_s"] for r in report["bellman_ford_pesos_negativos"]) / max(1, len(report["bellman_ford_pesos_negativos"])),
        sum(r["tempo_s"] for r in report["bellman_ford_ciclo_negativo"]) / max(1, len(report["bellman_ford_ciclo_negativo"])),
    ]
    cores = ["#1DB954", "#1DB954", "#1565C0", "#E53935", "#E53935"]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(algs, tempos, color=cores, edgecolor="black", linewidth=0.6)
    ax.set_title("Tempo médio de execução por algoritmo (Parte 2)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Tempo (segundos)", fontsize=11)
    ax.set_xlabel("Algoritmo", fontsize=11)
    for bar, t in zip(bars, tempos):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(tempos)*0.01,
                f"{t:.4f}s", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    plt.savefig(arquivo, dpi=120)
    plt.close()
    print(f"  Salvo: {arquivo}")


def vis_heatmap_distancias(D_sub, nos_sub, mapa_nome, arquivo, n_show=20):
    idx   = list(range(min(n_show, len(nos_sub))))
    D_vis = D_sub[np.ix_(idx, idx)]
    labels = [mapa_nome.get(nos_sub[i], nos_sub[i])[:15] for i in idx]

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(D_vis, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(idx)))
    ax.set_yticks(range(len(idx)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_title(f"Heatmap de distâncias entre {n_show} faixas (Parte 2)", fontsize=12, fontweight="bold")
    plt.colorbar(im, ax=ax, label="Distância euclidiana normalizada")
    plt.tight_layout()
    plt.savefig(arquivo, dpi=120)
    plt.close()
    print(f"  Salvo: {arquivo}")


def vis_bfs_camadas(niveis, mapa_nome, origem_nome, arquivo):
    """Histograma da distribuição de nós por camada BFS."""
    from collections import Counter
    cont = Counter(niveis.values())
    camadas = sorted(cont.keys())
    qtd     = [cont[c] for c in camadas]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(camadas, qtd, color="#1565C0", edgecolor="black", linewidth=0.5)
    ax.set_title(f"Nós por camada – BFS a partir de '{origem_nome[:30]}'",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Camada (distância em saltos)", fontsize=11)
    ax.set_ylabel("Número de nós", fontsize=11)
    plt.tight_layout()
    plt.savefig(arquivo, dpi=120)
    plt.close()
    print(f"  Salvo: {arquivo}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT, exist_ok=True)

    # 1. Carregar e amostrar
    df      = carregar_dataset()
    sample  = amostrar(df, N_SAMPLE)
    nos     = sample["track_id"].tolist()
    mapa_nome = dict(zip(sample["track_id"], sample["track_name"]))

    print(f"\nGrafo principal: {len(nos)} nós (amostra estratificada por gênero)")

    # 2. Normalizar e calcular matriz de distâncias
    print("Calculando matriz de distâncias…")
    X_norm = normalizar(sample)
    X_np   = X_norm.values
    D      = dist_matrix(X_np)

    media_dist = float(np.mean(D[D > 0]))
    print(f"  Distância média entre pares: {media_dist:.4f}")

    # 3. Grafo principal (pesos positivos – para BFS/DFS/Dijkstra)
    print(f"\nConstruindo grafo KNN (K={K_NEIGHBORS})…")
    grafo = construir_grafo_knn(nos, D.copy(), K_NEIGHBORS, offset=0.0)
    n_arestas = len(grafo.obter_todas_arestas())
    print(f"  |V|={len(nos)}, |E|={n_arestas}")

    # 4. Subgrafo para Bellman-Ford (menor, mais rápido)
    print(f"\nConstruindo subgrafo BF ({N_BF} nós)…")
    idx_bf = list(range(N_BF))
    nos_bf = [nos[i] for i in idx_bf]
    D_bf   = D[np.ix_(idx_bf, idx_bf)]

    # DAG com pesos negativos (sem ciclos possíveis → BF correto)
    grafo_bf_neg = construir_dag_negativo(nos_bf, D_bf.copy(), K=8)
    n_neg = len(grafo_bf_neg.obter_todas_arestas())
    n_neg_pesos = sum(1 for _, _, p in grafo_bf_neg.obter_todas_arestas() if p < 0)
    print(f"  DAG: |E|={n_neg}, arestas negativas={n_neg_pesos}")

    # Grafo com ciclo negativo artificial
    grafo_bf_ciclo, src_ciclo, dst_ciclo = grafo_com_ciclo_negativo(nos_bf, D_bf.copy())

    # 5. Escolher fontes e pares
    fontes_bfs = random.sample(nos, 3)
    fontes_dfs = random.sample(nos, 3)
    pares_dij  = [(random.choice(nos), random.choice(nos)) for _ in range(5)]

    # Para o DAG: encontra pares realmente alcançáveis via BFS no próprio DAG
    def _pares_alcancaveis(g, candidatos_orig, n_pares=3):
        pares = []
        for orig in candidatos_orig:
            ordem_dag, _, _ = bfs(g, orig)
            alcancaveis = [v for v in ordem_dag if v != orig]
            if alcancaveis:
                dest = alcancaveis[-1]  # nó mais distante em saltos
                pares.append((orig, dest))
            if len(pares) == n_pares:
                break
        return pares

    pares_bf = _pares_alcancaveis(grafo_bf_neg, nos_bf[:20], n_pares=3)

    # 6. Rodar algoritmos
    print("\n=== BFS ===")
    res_bfs = rodar_bfs(grafo, fontes_bfs, mapa_nome)

    print("\n=== DFS ===")
    res_dfs = rodar_dfs(grafo, fontes_dfs, mapa_nome)

    print("\n=== Dijkstra ===")
    res_dij = rodar_dijkstra(grafo, pares_dij, mapa_nome)

    print("\n=== Bellman-Ford (pesos negativos, sem ciclo negativo) ===")
    res_bf_neg = rodar_bellman_ford(grafo_bf_neg, pares_bf, mapa_nome, tag="pesos_negativos")

    print("\n=== Bellman-Ford (ciclo negativo detectado) ===")
    res_bf_ciclo = rodar_bellman_ford(
        grafo_bf_ciclo,
        [(src_ciclo, dst_ciclo)],
        mapa_nome,
        tag="ciclo_negativo",
    )

    # 7. Distribuição de graus do dataset completo (para descrição)
    print("\nCalculando distribuição de graus do dataset…")
    grau_todos = []
    for no in nos:
        grau_todos.append(len(grafo.obter_vizinhos_simples(no)))

    dist_graus = {}
    for g in grau_todos:
        dist_graus[g] = dist_graus.get(g, 0) + 1

    # 8. Relatório JSON
    report = {
        "dataset": {
            "fonte"           : "Spotify Tracks Dataset (Kaggle)",
            "nos_total_csv"   : len(df),
            "nos_amostra"     : len(nos),
            "arestas"         : n_arestas,
            "tipo"            : "dirigido, ponderado",
            "k_vizinhos"      : K_NEIGHBORS,
            "features_usadas" : FEATURES,
            "peso_formula"    : "distancia euclidiana normalizada (min-max) entre vetores de audio",
            "grau_medio"      : round(sum(grau_todos) / len(grau_todos), 2),
            "grau_max"        : max(grau_todos),
            "grau_min"        : min(grau_todos),
        },
        "bfs"                        : res_bfs,
        "dfs"                        : res_dfs,
        "dijkstra"                   : res_dij,
        "bellman_ford_pesos_negativos": res_bf_neg,
        "bellman_ford_ciclo_negativo" : res_bf_ciclo,
        "nota_bellman_ford": (
            f"BF sem ciclo negativo: DAG de {N_BF} nos, {n_neg} arestas, "
            f"{n_neg_pesos} arestas negativas (peso = dist - media_dist/2). "
            "DAG garante ausencia de ciclos. "
            "BF com ciclo negativo: subgrafo com 3 arestas artificiais a->b->c->a, peso -1.0 cada."
        ),
    }

    report_path = os.path.join(OUT, "parte2_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nRelatório salvo: {report_path}")

    # 9. Visualizações
    print("\n=== Gerando visualizações Parte 2 ===")

    vis_distribuicao_graus(
        grafo, nos,
        f"Distribuição de graus – Grafo Spotify ({len(nos)} faixas, K={K_NEIGHBORS})",
        os.path.join(OUT, "p2_vis1_distribuicao_graus.png"),
    )

    vis_tempo_algoritmos(
        report,
        os.path.join(OUT, "p2_vis2_tempo_algoritmos.png"),
    )

    vis_heatmap_distancias(
        D_bf, nos_bf, mapa_nome,
        os.path.join(OUT, "p2_vis3_heatmap_distancias.png"),
        n_show=20,
    )

    # BFS layers do primeiro fonte
    _, niveis_vis, _ = bfs(grafo, fontes_bfs[0])
    vis_bfs_camadas(
        niveis_vis, mapa_nome,
        mapa_nome.get(fontes_bfs[0], fontes_bfs[0]),
        os.path.join(OUT, "p2_vis4_bfs_camadas.png"),
    )

    print("\n=== Parte 2 concluída com sucesso ===")
    print(f"  Arquivo principal : {report_path}")
    print(f"  Visualizações     : p2_vis1..p2_vis4 em out/")


if __name__ == "__main__":
    main()
