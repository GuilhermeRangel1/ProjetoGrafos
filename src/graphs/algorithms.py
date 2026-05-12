"""
src/graphs/algorithms.py
Implementação própria dos algoritmos de grafos:
    - BFS  (Busca em Largura)
    - DFS  (Busca em Profundidade)
    - Dijkstra
    - Bellman-Ford
Proibido usar networkx, igraph ou similares.
"""

from __future__ import annotations

import heapq
import math
from collections import deque


# ---------------------------------------------------------------------------
# BFS — Busca em Largura
# ---------------------------------------------------------------------------

def bfs(adj: dict, start: str) -> dict[str, str | None]:
    """
    Percorre o grafo em largura a partir de 'start'.

    Parâmetros:
        adj   : dicionário de adjacência {nó: [(vizinho, peso), ...]}
        start : nó de origem

    Retorna:
        predecessores: {nó: predecessor} para reconstrução de caminhos.
                       O nó raiz tem predecessor None.
    """
    visited = {start}
    predecessors: dict[str, str | None] = {start: None}
    queue = deque([start])

    while queue:
        u = queue.popleft()
        for v, _ in adj.get(u, []):
            if v not in visited:
                visited.add(v)
                predecessors[v] = u
                queue.append(v)

    return predecessors


def bfs_path(adj: dict, start: str, end: str) -> list[str]:
    """
    Retorna o caminho entre start e end via BFS (menor número de arestas).
    Retorna lista vazia se não houver caminho.
    """
    predecessors = bfs(adj, start)
    if end not in predecessors:
        return []
    path, cur = [], end
    while cur is not None:
        path.append(cur)
        cur = predecessors[cur]
    return list(reversed(path))


# ---------------------------------------------------------------------------
# DFS — Busca em Profundidade
# ---------------------------------------------------------------------------

def dfs(adj: dict, start: str) -> dict[str, str | None]:
    """
    Percorre o grafo em profundidade a partir de 'start' (versão iterativa).

    Parâmetros:
        adj   : dicionário de adjacência {nó: [(vizinho, peso), ...]}
        start : nó de origem

    Retorna:
        predecessores: {nó: predecessor}
    """
    visited = set()
    predecessors: dict[str, str | None] = {start: None}
    stack = [start]

    while stack:
        u = stack.pop()
        if u in visited:
            continue
        visited.add(u)
        for v, _ in adj.get(u, []):
            if v not in visited:
                if v not in predecessors:
                    predecessors[v] = u
                stack.append(v)

    return predecessors


def dfs_path(adj: dict, start: str, end: str) -> list[str]:
    """
    Retorna um caminho entre start e end via DFS.
    Retorna lista vazia se não houver caminho.
    """
    predecessors = dfs(adj, start)
    if end not in predecessors:
        return []
    path, cur = [], end
    while cur is not None:
        path.append(cur)
        cur = predecessors[cur]
    return list(reversed(path))


# ---------------------------------------------------------------------------
# Dijkstra — Caminho mínimo com pesos não-negativos
# ---------------------------------------------------------------------------

def dijkstra(adj: dict, start: str, end: str) -> tuple[float, list[str]]:
    """
    Calcula o caminho de menor custo entre start e end.
    Exige que todos os pesos sejam não-negativos.

    Parâmetros:
        adj   : dicionário de adjacência {nó: [(vizinho, peso), ...]}
        start : nó de origem
        end   : nó de destino

    Retorna:
        (custo, caminho) onde:
            custo   = distância total mínima (float)
            caminho = lista de nós do percurso (vazia se sem caminho)
    """
    dist: dict[str, float] = {}
    prev: dict[str, str]   = {}

    # inicializar distâncias como infinito
    for node in adj:
        dist[node] = math.inf
    dist[start] = 0.0

    # heap: (distancia_acumulada, nó)
    heap = [(0.0, start)]

    while heap:
        d, u = heapq.heappop(heap)

        if d > dist.get(u, math.inf):
            continue  # entrada desatualizada no heap

        if u == end:
            break

        for v, w in adj.get(u, []):
            if w < 0:
                raise ValueError(
                    f"Dijkstra não suporta pesos negativos. "
                    f"Aresta {u}→{v} tem peso {w}. Use Bellman-Ford."
                )
            nd = dist[u] + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    # sem caminho
    if dist.get(end, math.inf) == math.inf:
        return math.inf, []

    # reconstruir caminho
    path, cur = [], end
    while cur in prev:
        path.append(cur)
        cur = prev[cur]
    path.append(start)
    return dist[end], list(reversed(path))


# ---------------------------------------------------------------------------
# Bellman-Ford — Caminho mínimo com pesos negativos (sem ciclos negativos)
# ---------------------------------------------------------------------------

def bellman_ford(adj: dict, nodes: set, start: str, end: str) -> tuple[float, list[str]]:
    """
    Calcula o caminho de menor custo entre start e end.
    Suporta pesos negativos. Detecta ciclos negativos.

    Parâmetros:
        adj   : dicionário de adjacência {nó: [(vizinho, peso), ...]}
        nodes : conjunto com todos os nós do grafo
        start : nó de origem
        end   : nó de destino

    Retorna:
        (custo, caminho)
    Lança ValueError se houver ciclo negativo alcançável.
    """
    dist: dict[str, float] = {n: math.inf for n in nodes}
    prev: dict[str, str]   = {}
    dist[start] = 0.0

    n = len(nodes)

    # relaxar |V| - 1 vezes
    for _ in range(n - 1):
        updated = False
        for u in adj:
            if dist[u] == math.inf:
                continue
            for v, w in adj[u]:
                if dist[u] + w < dist.get(v, math.inf):
                    dist[v] = dist[u] + w
                    prev[v] = u
                    updated = True
        if not updated:
            break  # convergiu antecipadamente

    # detectar ciclo negativo
    for u in adj:
        if dist[u] == math.inf:
            continue
        for v, w in adj[u]:
            if dist[u] + w < dist.get(v, math.inf):
                raise ValueError(
                    "Ciclo negativo detectado no grafo. "
                    "Bellman-Ford não pode garantir resultado correto."
                )

    if dist.get(end, math.inf) == math.inf:
        return math.inf, []

    path, cur = [], end
    while cur in prev:
        path.append(cur)
        cur = prev[cur]
    path.append(start)
    return dist[end], list(reversed(path))