import heapq
from collections import deque


def bfs(grafo, origem):
    visitados = {origem}
    niveis = {origem: 0}
    pais = {origem: None}
    fila = deque([origem])
    ordem_visita = []

    while fila:
        u = fila.popleft()
        ordem_visita.append(u)
        for v in grafo.obter_vizinhos_simples(u):
            if v not in visitados:
                visitados.add(v)
                niveis[v] = niveis[u] + 1
                pais[v] = u
                fila.append(v)

    return ordem_visita, niveis, pais


def dfs(grafo, origem):
    entrada = {}
    saida = {}
    tempo = [0]
    ordem_visita = []
    tem_ciclo = False
    arestas = {}

    def _push(u, pilha):
        cor[u] = 1
        tempo[0] += 1
        entrada[u] = tempo[0]
        ordem_visita.append(u)
        pilha.append((u, iter(grafo.obter_vizinhos_simples(u))))

    pilha = []
    _push(origem, pilha)

    while pilha:
        u, it = pilha[-1]
        try:
            v = next(it)
            cv = cor.get(v, 0)
            if cv == 0:
                arestas[(u, v)] = 'tree'
                _push(v, pilha)
            elif cv == 1:
                arestas[(u, v)] = 'back'
                tem_ciclo = True
            else:
                if entrada.get(u, 0) < entrada.get(v, 0):
                    arestas[(u, v)] = 'forward'
                else:
                    arestas[(u, v)] = 'cross'
        except StopIteration:
            cor[u] = 2
            tempo[0] += 1
            saida[u] = tempo[0]
            pilha.pop()

    return ordem_visita, tem_ciclo, arestas


def bellman_ford(grafo, origem, destino):
    nos = grafo.obter_todos_nos()
    n = len(nos)
    distancias = {no: float('inf') for no in nos}
    distancias[origem] = 0
    predecessores = {no: None for no in nos}

    arestas = grafo.obter_todas_arestas()

    for _ in range(n - 1):
        atualizado = False
        for u, v, peso in arestas:
            if distancias[u] != float('inf') and distancias[u] + peso < distancias[v]:
                distancias[v] = distancias[u] + peso
                predecessores[v] = u
                atualizado = True
        if not atualizado:
            break

    for u, v, peso in arestas:
        if distancias[u] != float('inf') and distancias[u] + peso < distancias[v]:
            return distancias, [], True

    caminho = []
    atual = destino
    visitados_rec = set()
    while atual is not None:
        if atual in visitados_rec:
            return distancias, [], True
        visitados_rec.add(atual)
        caminho.append(atual)
        atual = predecessores[atual]
    caminho.reverse()

    if not caminho or caminho[0] != origem:
        return distancias, [], False

    return distancias, caminho, False


def dijkstra(grafo, inicio, fim):
    distancias = {no: float('inf') for no in grafo.obter_todos_nos()}
    distancias[inicio] = 0
    
    predecessores = {no: None for no in grafo.obter_todos_nos()}
    
    fila = [(0, inicio)]
    
    while fila:
        custo_atual, u = heapq.heappop(fila)
        
        if custo_atual > distancias[u]:
            continue
            
        if u == fim:
            break
            
        for v, peso in grafo.obter_vizinhos_com_peso(u):
            if peso < 0:
                raise ValueError("Dijkstra não suporta pesos negativos!")
            
            novo_custo = custo_atual + peso
            if novo_custo < distancias[v]:
                distancias[v] = novo_custo
                predecessores[v] = u
                heapq.heappush(fila, (novo_custo, v))

    caminho = []
    atual = fim
    while atual is not None:
        caminho.append(atual)
        atual = predecessores[atual]
    caminho.reverse()

    if not caminho or caminho[0] != inicio:
        return float('inf'), []
        
    return distancias[fim], caminho