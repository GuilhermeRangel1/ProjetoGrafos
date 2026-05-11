import os
from pyvis.network import Network

def gerar_html_do_caminho(grafo, trajeto, origem, destino, pasta_saida):

    rede = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    
    for aeroporto in trajeto:
        rede.add_node(aeroporto, label=aeroporto, title=f"aeroportoporto {aeroporto}", color="#FF4500", size=35)
            
    for i in range(len(trajeto) - 1):
        passo_atual = trajeto[i]
        proximo_passo = trajeto[i+1]
        
        distancia_do_voo = 0
        vizinhos = grafo.obter_vizinhos_com_peso(passo_atual)
        
        for vizinho, peso in vizinhos:
            if vizinho == proximo_passo:
                distancia_do_voo = peso
                break
        rede.add_edge(passo_atual, proximo_passo, color="red", width=4, label=str(distancia_do_voo))
                    
    nome_arquivo = f"arvore_percurso_{origem}_para_{destino}.html"
    caminho_salvar = os.path.join(pasta_saida, nome_arquivo)
    
    rede.save_graph(caminho_salvar)