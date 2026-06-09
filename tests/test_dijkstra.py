import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graphs.graph import Grafo
from graphs.algorithms import dijkstra


def _grafo_simples():
    #  A -1- B -2- C
    #   \         /
    #    ---4----
    g = Grafo(dirigido=False)
    g.adicionar_aresta('A', 'B', 1)
    g.adicionar_aresta('B', 'C', 2)
    g.adicionar_aresta('A', 'C', 4)
    return g


def test_dijkstra_caminho_correto():
    g = _grafo_simples()
    custo, caminho = dijkstra(g, 'A', 'C')
    assert custo == 3
    assert caminho == ['A', 'B', 'C']


def test_dijkstra_prefere_caminho_mais_curto():
    g = _grafo_simples()
    custo, _ = dijkstra(g, 'A', 'C')
    # Direto A->C custa 4; via B custa 3
    assert custo == 3


def test_dijkstra_mesmo_no():
    g = _grafo_simples()
    custo, caminho = dijkstra(g, 'A', 'A')
    assert custo == 0
    assert caminho == ['A']


def test_dijkstra_no_inalcancavel():
    g = _grafo_simples()
    g.adicionar_no('Z')
    custo, caminho = dijkstra(g, 'A', 'Z')
    assert custo == float('inf')
    assert caminho == []


def test_dijkstra_rejeita_peso_negativo():
    g = Grafo(dirigido=False)
    g.adicionar_aresta('A', 'B', -1)
    with pytest.raises(ValueError):
        dijkstra(g, 'A', 'B')


def test_dijkstra_grafo_maior():
    #  A-1-B-1-C-1-D
    #      |       |
    #      --5-----
    g = Grafo(dirigido=False)
    g.adicionar_aresta('A', 'B', 1)
    g.adicionar_aresta('B', 'C', 1)
    g.adicionar_aresta('C', 'D', 1)
    g.adicionar_aresta('B', 'D', 5)
    custo, caminho = dijkstra(g, 'A', 'D')
    assert custo == 3
    assert caminho == ['A', 'B', 'C', 'D']
