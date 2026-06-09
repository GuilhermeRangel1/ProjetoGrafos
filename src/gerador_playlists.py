import os
import sys
import pandas as pd
import random

sys.path.insert(0, os.path.dirname(__file__))
from graphs.algorithms import bfs, dfs
from analise_parte2 import carregar_dataset, amostrar, normalizar, dist_matrix, construir_grafo_knn

BASE = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.join(BASE, "out")

def gerar_playlist_bfs(grafo, origem, tamanho, mapa_nome):
    ordem_visita, niveis, pais = bfs(grafo, origem)
    playlist_ids = ordem_visita[:tamanho]
    return [mapa_nome.get(tid, tid) for tid in playlist_ids]

def gerar_playlist_dfs(grafo, origem, tamanho, mapa_nome):
    ordem_visita, ciclo, arestas = dfs(grafo, origem)
    playlist_ids = ordem_visita[:tamanho]
    return [mapa_nome.get(tid, tid) for tid in playlist_ids]

def main():
    print("carregando dataset...")

    df = carregar_dataset()
    sample = amostrar(df, 2000)

    nos = sample["track_id"].tolist()
    mapa_nome = dict(zip(sample["track_id"], sample["track_name"]))
    mapa_artista = dict(zip(sample["track_id"], sample["artists"])) if "artists" in sample.columns else {}

    def formatar_nome(tid):
        nome = mapa_nome.get(tid, tid)
        artista = mapa_artista.get(tid, "desconhecido")
        if artista != "desconhecido":
            return f"{nome} - {artista}"
        return nome

    mapa_formatado = {tid: formatar_nome(tid) for tid in nos}

    print("calculando similaridades...")
    X_norm = normalizar(sample)
    D = dist_matrix(X_norm.values)

    print("construindo grafo...")
    grafo = construir_grafo_knn(nos, D, K=10)

    origem = random.choice(nos)
    tamanho_playlist = 15

    print(f"\nmúsica inicial: {mapa_formatado[origem]}")

    playlist_bfs = gerar_playlist_bfs(grafo, origem, tamanho_playlist, mapa_formatado)
    playlist_dfs = gerar_playlist_dfs(grafo, origem, tamanho_playlist, mapa_formatado)

    print("\n" + "="*50)
    print("playlist bfs: transição suave, em camadas")
    print("começa pelas músicas mais parecidas e vai se afastando aos poucos.")
    print("="*50)
    for i, musica in enumerate(playlist_bfs, 1):
        print(f"{i}. {musica}")

    print("\n" + "="*50)
    print("playlist dfs: mergulho profundo")
    print("segue uma cadeia de conexões, levando por uma jornada musical imprevisível.")
    print("="*50)
    for i, musica in enumerate(playlist_dfs, 1):
        print(f"{i}. {musica}")

    os.makedirs(OUT, exist_ok=True)
    caminho_saida = os.path.join(OUT, "playlists_geradas.txt")
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(f"música raiz: {mapa_formatado[origem]}\n\n")
        f.write("=== playlist bfs — transição suave ===\n")
        for i, m in enumerate(playlist_bfs, 1):
            f.write(f"{i}. {m}\n")
        f.write("\n=== playlist dfs: mergulho profundo ===\n")
        for i, m in enumerate(playlist_dfs, 1):
            f.write(f"{m}\n")

    print(f"\nplaylists salvas em: {caminho_saida}")

if __name__ == "__main__":
    main()
