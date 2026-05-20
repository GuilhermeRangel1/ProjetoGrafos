import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graphs.graph import Grafo
from graphs.algorithms import bfs


def _grafo_camadas():
    """   A
        / \
       B   C
      / \
     D   E        """
    g = Grafo(dirigido=False)
    for u, v in [('A', 'B'), ('A', 'C'), ('B', 'D'), ('B', 'E')]:
        g.adicionar_aresta(u, v)
    return g


def test_bfs_niveis_corretos():
    g = _grafo_camadas()
    _, niveis, _ = bfs(g, 'A')
    assert niveis['A'] == 0
    assert niveis['B'] == 1
    assert niveis['C'] == 1
    assert niveis['D'] == 2
    assert niveis['E'] == 2


def test_bfs_ordem_largura():
    g = _grafo_camadas()
    ordem, _, _ = bfs(g, 'A')
    # A deve vir antes de B e C; B e C antes de D e E
    assert ordem.index('A') < ordem.index('B')
    assert ordem.index('A') < ordem.index('C')
    assert ordem.index('B') < ordem.index('D')
    assert ordem.index('B') < ordem.index('E')


def test_bfs_pais():
    g = _grafo_camadas()
    _, _, pais = bfs(g, 'A')
    assert pais['A'] is None
    assert pais['B'] == 'A'
    assert pais['C'] == 'A'
    assert pais['D'] == 'B'
    assert pais['E'] == 'B'


def test_bfs_no_isolado_nao_visitado():
    g = _grafo_camadas()
    g.adicionar_no('Z')  # nó sem arestas
    ordem, niveis, _ = bfs(g, 'A')
    assert 'Z' not in ordem
    assert 'Z' not in niveis


def test_bfs_grafo_linear():
    g = Grafo(dirigido=False)
    for u, v in [('1', '2'), ('2', '3'), ('3', '4')]:
        g.adicionar_aresta(u, v)
    _, niveis, _ = bfs(g, '1')
    assert niveis == {'1': 0, '2': 1, '3': 2, '4': 3}
