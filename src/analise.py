import pandas as pd
import matplotlib.pyplot as plt
import os

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

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(__file__))
    caminho_graus = os.path.join(base_path, 'out', 'graus.csv')
    pasta_saida = os.path.join(base_path, 'out')
    plot_ranking_hubs(caminho_graus, pasta_saida)