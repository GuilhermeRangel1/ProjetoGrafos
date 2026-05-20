import heapq

def dijkstra(grafo, origem, destino):
    custos = {}
    anterior = {}
    listaAeroportos = grafo.listaAeroportos()
    
    for vertice in listaAeroportos:
        custos[vertice] = float('inf') 
        anterior[vertice] = None      
    
    if origem not in custos or destino not in custos:
        return float('inf'), []

    custos[origem] = 0
    fila = [(0, origem)]

    while fila:
        distAtual, vertice1 = heapq.heappop(fila)
        if distAtual > custos[vertice1]:
            continue
        if vertice1 == destino:
            break

        for vertice2, peso in grafo.listaVizinhoPesos(vertice1):
            if peso < 0:
                raise ValueError("Peso negativo")

            novoCusto = distAtual + peso
            
            if novoCusto < custos[vertice2]:
                custos[vertice2] = novoCusto
                anterior[vertice2] = vertice1
                heapq.heappush(fila, (novoCusto, vertice2))

    caminho = []
    passo = destino
    
    while passo is not None:
        caminho.append(passo)
        passo = anterior[passo]
        
    caminho.reverse() 

    if len(caminho) == 0 or caminho[0] != origem:
        return float('inf'), []

    return custos[destino], caminho