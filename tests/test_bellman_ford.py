import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graphs.graph import Grafo
from graphs.algorithms import bellman_ford


def _grafo_peso_negativo():
    # A -1-> B -(-2)-> C -1-> D
    # A --------4-------> D
    # Caminho ótimo: A->B->C->D = 1 + (-2) + 1 = 0  (melhor que A->D=4)
    g = Grafo(dirigido=True)
    g.adicionar_aresta('A', 'B', 1)
    g.adicionar_aresta('B', 'C', -2)
    g.adicionar_aresta('C', 'D', 1)
    g.adicionar_aresta('A', 'D', 4)
    return g


def _grafo_ciclo_negativo():
    # A->B->C->B (ciclo B->C->B com peso -1 + (-1) = -2)
    g = Grafo(dirigido=True)
    g.adicionar_aresta('A', 'B', 1)
    g.adicionar_aresta('B', 'C', -1)
    g.adicionar_aresta('C', 'B', -1)
    g.adicionar_aresta('C', 'D', 1)
    return g


def test_bellman_ford_peso_negativo_distancia_correta():
    g = _grafo_peso_negativo()
    distancias, caminho, tem_ciclo = bellman_ford(g, 'A', 'D')
    assert tem_ciclo is False
    assert distancias['D'] == 0
    assert caminho == ['A', 'B', 'C', 'D']


def test_bellman_ford_sem_ciclo_negativo():
    g = _grafo_peso_negativo()
    _, _, tem_ciclo = bellman_ford(g, 'A', 'D')
    assert tem_ciclo is False


def test_bellman_ford_detecta_ciclo_negativo():
    g = _grafo_ciclo_negativo()
    _, _, tem_ciclo = bellman_ford(g, 'A', 'D')
    assert tem_ciclo is True


def test_bellman_ford_pesos_positivos_equivale_dijkstra():
    # Com pesos positivos, BF deve dar o mesmo resultado que Dijkstra
    from graphs.algorithms import dijkstra
    g = Grafo(dirigido=True)
    g.adicionar_aresta('A', 'B', 2)
    g.adicionar_aresta('B', 'C', 3)
    g.adicionar_aresta('A', 'C', 10)
    dist_bf, caminho_bf, ciclo = bellman_ford(g, 'A', 'C')
    custo_dj, caminho_dj = dijkstra(g, 'A', 'C')
    assert ciclo is False
    assert dist_bf['C'] == custo_dj
    assert caminho_bf == caminho_dj


def test_bellman_ford_no_inalcancavel():
    g = Grafo(dirigido=True)
    g.adicionar_aresta('A', 'B', 1)
    g.adicionar_no('Z')
    distancias, caminho, tem_ciclo = bellman_ford(g, 'A', 'Z')
    assert distancias['Z'] == float('inf')
    assert caminho == []
    assert tem_ciclo is False
