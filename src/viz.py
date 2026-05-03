import os
from pyvis.network import Network

def exportar_arvore_percurso_html(grafo, caminho1, caminho2, pasta_saida):
    """
    Constrói a árvore de caminhos a partir das rotas fornecidas e salva como HTML interativo (Pyvis).
    """
    net = Network(height="700px", width="100%", bgcolor="#ffffff", font_color="black", directed=False)
    
    def extrair_arestas(caminho):
        arestas = []
        if caminho:
            for i in range(len(caminho) - 1):
                arestas.append((caminho[i], caminho[i+1]))
        return arestas

    arestas_destaque = extrair_arestas(caminho1) + extrair_arestas(caminho2)
    nos_adicionados = set()

    for u, v in arestas_destaque:
        if u not in nos_adicionados:
            net.add_node(u, label=u, title=f"Aeroporto {u}", color="#87CEFA", size=25)
            nos_adicionados.add(u)
        if v not in nos_adicionados:
            net.add_node(v, label=v, title=f"Aeroporto {v}", color="#87CEFA", size=25)
            nos_adicionados.add(v)
            
        peso = next((w for viz, w in grafo.obter_vizinhos_com_peso(u) if viz == v), 0)
        
        net.add_edge(u, v, value=3, title=f"Distância/Custo: {peso}", label=str(peso), color="red")

    net.repulsion(node_distance=150, spring_length=100)

    caminho_arquivo = os.path.join(pasta_saida, 'arvore_percurso.html')
    
    net.save_graph(caminho_arquivo)
    
    print(f"OK: arvore_percurso.html gerado com sucesso em {caminho_arquivo}")