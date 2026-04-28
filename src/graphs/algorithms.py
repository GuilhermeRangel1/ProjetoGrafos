import heapq

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