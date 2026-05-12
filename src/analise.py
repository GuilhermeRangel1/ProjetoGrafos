import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from pyvis.network import Network

def gerar_vis1_ranking_hubs(caminho_graus, pasta_saida):
    
    tabela_graus = pd.read_csv(caminho_graus, encoding='utf-8')
    
    top_10 = tabela_graus.nlargest(10, 'grau')
    
    top_10 = top_10.sort_values(by='grau', ascending=True)
    
    lista_aeroportos = top_10['aeroporto'].tolist()
    lista_graus = top_10['grau'].tolist()
    
    plt.figure(figsize=(10, 6))
    
    plt.barh(lista_aeroportos, lista_graus, color='#4682B4', edgecolor='black')
    
    plt.title('Top 10 aeroportos mais conectados', fontsize=14, fontweight='bold')
    plt.xlabel('Número de conexões diretas(grau)', fontsize=12)
    plt.ylabel('Aeroporto(código IATA)', fontsize=12)
    
    for i in range(len(lista_aeroportos)):
        valor = lista_graus[i]
        plt.text(valor + 0.2, i, str(valor), va='center', fontsize=10)
        
    plt.xlim(0, max(lista_graus) + 2)
    
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    nome_arquivo = 'vis1_ranking_hubs.png'
    caminho_salvar = os.path.join(pasta_saida, nome_arquivo)
    plt.savefig(caminho_salvar, format='png', dpi=300)
    plt.close()
    
    print(f"Imagem salva em {caminho_salvar}")

def gerar_vis2_distribuicao_graus(caminho_graus, pasta_saida):
    
    tabela_graus = pd.read_csv(caminho_graus, encoding='utf-8')
    
    lista_graus = tabela_graus['grau'].tolist()
    
    plt.figure(figsize=(10, 6))
    
    plt.hist(lista_graus, bins=10, color='#2E8B57', edgecolor='black', alpha=0.8)
    
    plt.title('Distribuição do número de conexões(graus)', fontsize=14, fontweight='bold')
    plt.xlabel('Número de conexões diretas(grau)', fontsize=12)
    plt.ylabel('quantidade de aeroportos', fontsize=12)
    
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    nome_arquivo = 'vis2_distribuicao_graus.png'
    caminho_salvar = os.path.join(pasta_saida, nome_arquivo)
    plt.savefig(caminho_salvar, format='png', dpi=300)
    plt.close()
    
    print(f"Imagem salva em {caminho_salvar}")


def gerar_vis3_comparacao_regioes(caminho_regioes, pasta_saida):
    
    with open(caminho_regioes, 'r', encoding='utf-8') as arquivo:
        dados_regioes = json.load(arquivo)
        
    lista_nomes_regioes = []
    lista_ordem = []
    lista_tamanho = []
    
    for regiao, valores in dados_regioes.items():
        lista_nomes_regioes.append(regiao)
        lista_ordem.append(valores['ordem'])
        lista_tamanho.append(valores['tamanho'])
        
    posicoes_x = list(range(len(lista_nomes_regioes)))
    
    posicoes_barra_azul = []
    posicoes_barra_laranja = []
    
    for x in posicoes_x:
        posicoes_barra_azul.append(x - 0.2)
        posicoes_barra_laranja.append(x + 0.2)
        
    plt.figure(figsize=(10, 6))
    
    plt.bar(posicoes_barra_azul, lista_ordem, width=0.4, label='Quantidade de aeroportos(ordem)', color='#4682B4', edgecolor='black')
    plt.bar(posicoes_barra_laranja, lista_tamanho, width=0.4, label='Quantidade de voos internos(tamanho)', color='#FF8C00', edgecolor='black')
    
    plt.title('Infraestrutura aérea por região: aeroportos vs voos internos', fontsize=14, fontweight='bold')
    plt.xlabel('Região do Brasil', fontsize=12)
    plt.ylabel('Quantidade', fontsize=12)
    
    plt.xticks(posicoes_x, lista_nomes_regioes)
    plt.legend()
    
    for i in range(len(lista_nomes_regioes)):
        plt.text(posicoes_barra_azul[i], lista_ordem[i] + 0.2, str(lista_ordem[i]), ha='center', fontsize=10)
        plt.text(posicoes_barra_laranja[i], lista_tamanho[i] + 0.2, str(lista_tamanho[i]), ha='center', fontsize=10)
        
    valor_maximo = max(max(lista_ordem), max(lista_tamanho))
    plt.ylim(0, valor_maximo + 2)
    
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    nome_arquivo = 'vis3_comparacao_regioes.png'
    caminho_salvar = os.path.join(pasta_saida, nome_arquivo)
    plt.savefig(caminho_salvar, format='png', dpi=300)
    plt.close()
    
    print(f"Imagem salva em {caminho_salvar}")

def gerar_vis4_subgrafo_hubs(caminho_adj, caminho_graus, pasta_saida):
    
    tabela_graus = pd.read_csv(caminho_graus, encoding='utf-8')
    
    lista_hubs = []
    dicionario_graus = {}
    
    for _, linha in tabela_graus.iterrows():
        aeroporto = str(linha['aeroporto']).strip()
        grau = int(linha['grau'])
        
        if grau >= 10:
            lista_hubs.append(aeroporto)
            dicionario_graus[aeroporto] = grau
            
    tabela_adj = pd.read_csv(caminho_adj, encoding='utf-8')
    conexoes_dos_hubs = []
    
    for _, linha in tabela_adj.iterrows():
        origem = str(linha['origem']).strip()
        destino = str(linha['destino']).strip()
        peso = float(linha['peso'])
        
        if origem in lista_hubs and destino in lista_hubs:
            conexoes_dos_hubs.append((origem, destino, peso))
            
    rede = Network(height="700px", width="100%", bgcolor="#ffffff", font_color="black", directed=False)
    
    for hub in lista_hubs:
        tamanho_no = dicionario_graus[hub] * 2  
        texto_mouse = f"Aeroporto {hub} (Grau: {dicionario_graus[hub]})"
        
        rede.add_node(hub, label=hub, title=texto_mouse, color="#FF6347", size=tamanho_no)

    for origem, destino, peso in conexoes_dos_hubs:
        texto_linha = f"Distância: {peso} km"
        rede.add_edge(origem, destino, value=1, title=texto_linha, color="#A9A9A9")

    rede.repulsion(node_distance=200, spring_length=150)
    
    nome_arquivo = 'vis4_subgrafo_hubs.html'
    caminho_salvar = os.path.join(pasta_saida, nome_arquivo)
    rede.save_graph(caminho_salvar)
    
    print(f"HTML salvo em {caminho_salvar}")

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(__file__))
    
    caminho_graus = os.path.join(base_path, 'out', 'graus.csv')
    caminho_regioes = os.path.join(base_path, 'out', 'regioes.json')
    caminho_adj = os.path.join(base_path, 'data', 'adjacencias_aeroportos.csv')
    
    pasta_saida = os.path.join(base_path, 'out')
    
    gerar_vis1_ranking_hubs(caminho_graus, pasta_saida)
    gerar_vis2_distribuicao_graus(caminho_graus, pasta_saida)
    gerar_vis3_comparacao_regioes(caminho_regioes, pasta_saida)
    gerar_vis4_subgrafo_hubs(caminho_adj, caminho_graus, pasta_saida)
    