import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graphs.graph import Grafo
from graphs.algorithms import dfs


def _grafo_sem_ciclo():
    # DAG: A->B->D, A->C->D
    g = Grafo(dirigido=True)
    for u, v in [('A', 'B'), ('A', 'C'), ('B', 'D'), ('C', 'D')]:
        g.adicionar_aresta(u, v)
    return g


def _grafo_com_ciclo():
    # A->B->C->A
    g = Grafo(dirigido=True)
    for u, v in [('A', 'B'), ('B', 'C'), ('C', 'A')]:
        g.adicionar_aresta(u, v)
    return g


def test_dfs_detecta_ciclo():
    g = _grafo_com_ciclo()
    _, tem_ciclo, _ = dfs(g, 'A')
    assert tem_ciclo is True


def test_dfs_sem_ciclo():
    g = _grafo_sem_ciclo()
    _, tem_ciclo, _ = dfs(g, 'A')
    assert tem_ciclo is False


def test_dfs_classifica_back_edge():
    g = _grafo_com_ciclo()
    _, _, arestas = dfs(g, 'A')
    tipos = set(arestas.values())
    assert 'back' in tipos


def test_dfs_classifica_tree_edge():
    g = _grafo_sem_ciclo()
    _, _, arestas = dfs(g, 'A')
    assert arestas[('A', 'B')] == 'tree'
    assert arestas[('B', 'D')] == 'tree'


def test_dfs_visita_origem():
    g = _grafo_sem_ciclo()
    ordem, _, _ = dfs(g, 'A')
    assert ordem[0] == 'A'


def test_dfs_grafo_nao_dirigido_com_ciclo():
    # Triângulo não-dirigido deve ter ciclo
    g = Grafo(dirigido=False)
    for u, v in [('X', 'Y'), ('Y', 'Z'), ('Z', 'X')]:
        g.adicionar_aresta(u, v)
    _, tem_ciclo, _ = dfs(g, 'X')
    assert tem_ciclo is True
