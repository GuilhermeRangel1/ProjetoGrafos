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
    """
    Gera uma playlist usando Busca em Largura (BFS).
    Característica: Explora as músicas mais similares e gradualmente
    se afasta em camadas. Cria uma transição mais suave.
    """
    ordem_visita, niveis, pais = bfs(grafo, origem)
    playlist_ids = ordem_visita[:tamanho]
    playlist_nomes = [mapa_nome.get(tid, tid) for tid in playlist_ids]
    return playlist_nomes

def gerar_playlist_dfs(grafo, origem, tamanho, mapa_nome):
    """
    Gera uma playlist usando Busca em Profundidade (DFS).
    Característica: Mergulha profundamente em uma cadeia de similaridades
    (uma música leva à outra), podendo terminar em um estilo diferente.
    Uma jornada de "rabbit hole" musical.
    """
    ordem_visita, ciclo, arestas = dfs(grafo, origem)
    playlist_ids = ordem_visita[:tamanho]
    playlist_nomes = [mapa_nome.get(tid, tid) for tid in playlist_ids]
    return playlist_nomes

def main():
    print("Iniciando Gerador Automático de Playlists...")
    
    # 1. Preparar os dados (usando lógica existente na analise_parte2.py)
    df = carregar_dataset()
    sample = amostrar(df, 2000) # Trabalhando com uma amostra para construir o grafo rapidamente
    
    nos = sample["track_id"].tolist()
    mapa_nome = dict(zip(sample["track_id"], sample["track_name"]))
    mapa_artista = dict(zip(sample["track_id"], sample["artists"])) if "artists" in sample.columns else {}
    
    # Para o print ficar mais legal, adicionamos o artista se disponível
    def formatar_nome(tid):
        nome = mapa_nome.get(tid, tid)
        artista = mapa_artista.get(tid, "Desconhecido")
        if artista != "Desconhecido":
            return f"{nome} - {artista}"
        return nome

    mapa_formatado = {tid: formatar_nome(tid) for tid in nos}

    print("Calculando similaridades entre as músicas...")
    X_norm = normalizar(sample)
    D = dist_matrix(X_norm.values)
    
    # 2. Construir o Grafo (Músicas conectadas às suas 10 mais similares)
    print("Construindo grafo de músicas similares...")
    grafo = construir_grafo_knn(nos, D, K=10)
    
    # Escolher uma música inicial aleatória para a demonstração
    origem = random.choice(nos)
    tamanho_playlist = 15
    
    print(f"\nMúsica inicial escolhida: {mapa_formatado[origem]}")
    
    # 3. Gerar as Playlists
    playlist_bfs = gerar_playlist_bfs(grafo, origem, tamanho_playlist, mapa_formatado)
    playlist_dfs = gerar_playlist_dfs(grafo, origem, tamanho_playlist, mapa_formatado)
    
    # 4. Exibir e Salvar
    print("\n" + "="*50)
    print("PLAYLIST BFS (Transição Suave / Em Camadas)")
    print("Esta playlist explora músicas muito parecidas com a original antes de mudar o estilo.")
    print("="*50)
    for i, musica in enumerate(playlist_bfs, 1):
        print(f"{i}. {musica}")
        
    print("\n" + "="*50)
    print("PLAYLIST DFS (Mergulho Profundo / Jornada)")
    print("Esta playlist segue uma cadeia de conexões, levando você por uma jornada musical imprevisível.")
    print("="*50)
    for i, musica in enumerate(playlist_dfs, 1):
        print(f"{i}. {musica}")
        
    # Salvar em arquivo texto
    os.makedirs(OUT, exist_ok=True)
    caminho_saida = os.path.join(OUT, "playlists_geradas.txt")
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(f"Música Raiz: {mapa_formatado[origem]}\n\n")
        f.write("=== PLAYLIST BFS (Transição Suave) ===\n")
        for i, m in enumerate(playlist_bfs, 1):
            f.write(f"{i}. {m}\n")
            
        f.write("\n=== PLAYLIST DFS (Jornada Profunda) ===\n")
        for i, m in enumerate(playlist_dfs, 1):
            f.write(f"{i}. {m}\n")
            
    print(f"\nPlaylists salvas em: {caminho_saida}")

if __name__ == "__main__":
    main()
