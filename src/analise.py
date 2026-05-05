import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from pyvis.network import Network

def plot_ranking_hubs(caminho_graus, pasta_saida):
    """
    Gera um gráfico de barras horizontais com os 10 aeroportos de maior grau.
    """
    print("Gerando Visualização 1: Ranking de Hubs...")
    
    df = pd.read_csv(caminho_graus, encoding='utf-8')
    
    top_10 = df.nlargest(10, 'grau').sort_values(by='grau', ascending=True)
    
    plt.figure(figsize=(10, 6))
    plt.barh(top_10['aeroporto'], top_10['grau'], color='#4682B4', edgecolor='black')
    
    plt.title('Top 10 Aeroportos Mais Conectados (Hubs)', fontsize=14, fontweight='bold')
    plt.xlabel('Número de Conexões Diretas (Grau)', fontsize=12)
    plt.ylabel('Aeroporto (IATA)', fontsize=12)
    
    for index, value in enumerate(top_10['grau']):
        plt.text(value + 0.2, index, str(value), va='center', fontsize=10)
    
    plt.xlim(0, top_10['grau'].max() + 2)
    
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    caminho_arquivo = os.path.join(pasta_saida, 'vis1_ranking_hubs.png')
    plt.savefig(caminho_arquivo, format='png', dpi=300)
    plt.close()
    
    print(f"OK: {caminho_arquivo} gerado com sucesso.")

def plot_distribuicao_graus(caminho_graus, pasta_saida):
    """
    Gera um histograma mostrando a distribuição de graus na rede.
    """
    print("Gerando Visualização 2: Distribuicao de Graus...")
    
    df = pd.read_csv(caminho_graus, encoding='utf-8')
    
    plt.figure(figsize=(10, 6))
    
    plt.hist(df['grau'], bins=10, color='#2E8B57', edgecolor='black', alpha=0.8)
    
    plt.title('Distribuição do Número de Conexões (Graus)', fontsize=14, fontweight='bold')
    plt.xlabel('Número de Conexões Diretas (Grau)', fontsize=12)
    plt.ylabel('Quantidade de Aeroportos (Frequência)', fontsize=12)
    
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    caminho_arquivo = os.path.join(pasta_saida, 'vis2_distribuicao_graus.png')
    plt.savefig(caminho_arquivo, format='png', dpi=300)
    plt.close()
    
    print(f"OK: {caminho_arquivo} gerado com sucesso.")

def plot_comparacao_regioes(caminho_regioes, pasta_saida):
    """
    Gera um gráfico de barras agrupadas comparando ordem e tamanho por região.
    """
    print("Gerando Visualização 3: Comparacao por Regioes...")
    
    with open(caminho_regioes, 'r', encoding='utf-8') as f:
        dados = json.load(f)
        
    regioes = list(dados.keys())
    ordem = [dados[r]['ordem'] for r in regioes]
    tamanho = [dados[r]['tamanho'] for r in regioes]
    
    x = list(range(len(regioes)))
    x_ordem = [i - 0.2 for i in x]
    x_tamanho = [i + 0.2 for i in x]
    
    plt.figure(figsize=(10, 6))
    
    plt.bar(x_ordem, ordem, width=0.4, label='Qtd. Aeroportos (Ordem)', color='#4682B4', edgecolor='black')
    plt.bar(x_tamanho, tamanho, width=0.4, label='Voos Internos (Tamanho)', color='#FF8C00', edgecolor='black')
    
    plt.title('Infraestrutura Aérea por Região: Aeroportos vs Voos Internos', fontsize=14, fontweight='bold')
    plt.xlabel('Região', fontsize=12)
    plt.ylabel('Quantidade', fontsize=12)
    plt.xticks(x, regioes)
    plt.legend()
    
    for i in range(len(regioes)):
        plt.text(x_ordem[i], ordem[i] + 0.2, str(ordem[i]), ha='center', fontsize=10)
        plt.text(x_tamanho[i], tamanho[i] + 0.2, str(tamanho[i]), ha='center', fontsize=10)
        
    plt.ylim(0, max(max(ordem), max(tamanho)) + 2)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    caminho_arquivo = os.path.join(pasta_saida, 'vis3_comparacao_regioes.png')
    plt.savefig(caminho_arquivo, format='png', dpi=300)
    plt.close()
    
    print(f"OK: {caminho_arquivo} gerado com sucesso.")

def plot_subgrafo_hubs(caminho_adj, caminho_graus, pasta_saida):
    """
    Gera um subgrafo interativo em HTML apenas com os aeroportos de grau >= 10.
    """
    print("Gerando Visualização 4: Subgrafo Interativo dos Hubs...")
    
    df_graus = pd.read_csv(caminho_graus, encoding='utf-8')
    hubs = df_graus[df_graus['grau'] >= 10]
    lista_hubs = hubs['aeroporto'].tolist()
    
    dict_graus = dict(zip(hubs['aeroporto'], hubs['grau']))

    df_adj = pd.read_csv(caminho_adj, encoding='utf-8')
    df_hubs_adj = df_adj[(df_adj['origem'].isin(lista_hubs)) & (df_adj['destino'].isin(lista_hubs))]

    net = Network(height="700px", width="100%", bgcolor="#ffffff", font_color="black", directed=False)
    
    for hub in lista_hubs:
        tamanho_no = dict_graus[hub] * 2
        net.add_node(hub, label=hub, title=f"Aeroporto {hub} (Grau: {dict_graus[hub]})", 
                     color="#FF6347", size=tamanho_no)

    for _, linha in df_hubs_adj.iterrows():
        origem = str(linha['origem']).strip()
        destino = str(linha['destino']).strip()
        peso = float(linha['peso'])
        net.add_edge(origem, destino, value=1, title=f"Distância: {peso}", color="#A9A9A9")

    net.repulsion(node_distance=200, spring_length=150)
    
    caminho_arquivo = os.path.join(pasta_saida, 'vis4_subgrafo_hubs.html')
    net.save_graph(caminho_arquivo)
    
    print(f"OK: {caminho_arquivo} gerado com sucesso.")

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(__file__))
    caminho_graus = os.path.join(base_path, 'out', 'graus.csv')
    caminho_regioes = os.path.join(base_path, 'out', 'regioes.json')
    caminho_adj = os.path.join(base_path, 'data', 'adjacencias_aeroportos.csv')
    pasta_saida = os.path.join(base_path, 'out')
    
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
        
    plot_ranking_hubs(caminho_graus, pasta_saida)
    plot_distribuicao_graus(caminho_graus, pasta_saida)
    plot_comparacao_regioes(caminho_regioes, pasta_saida)
    plot_subgrafo_hubs(caminho_adj, caminho_graus, pasta_saida)
    print("\n--- Etapa 8: Todas as visualizacoes geradas com sucesso! ---")