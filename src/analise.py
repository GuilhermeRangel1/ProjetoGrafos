import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import json
from pyvis.network import Network

COR_FUNDO = "#0d0d14"
COR_PLANO = "#13131f"
COR_TEXTO = "#e0e0f0"
COR_GRADE = "#252535"
COR_DESTAQUE = "#f5a623" 

def aplicar_estilo_escuro(fig, ax):
    fig.patch.set_facecolor(COR_FUNDO)
    ax.set_facecolor(COR_PLANO)
    ax.tick_params(colors=COR_TEXTO, labelsize=9)
    
    for borda in ax.spines.values():
        borda.set_edgecolor(COR_GRADE)
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    ax.xaxis.label.set_color(COR_TEXTO)
    ax.yaxis.label.set_color(COR_TEXTO)
    ax.title.set_color(COR_TEXTO)
    ax.grid(color=COR_GRADE, linewidth=0.6, linestyle="--", alpha=0.5)


def gerar_vis1_ranking_hubs(caminho_graus, pasta_saida):
    tabela = pd.read_csv(caminho_graus, encoding='utf-8')
    top_10 = tabela.nlargest(10, 'grau').sort_values(by='grau', ascending=True)
    
    aeroportos = top_10['aeroporto'].tolist()
    graus = top_10['grau'].tolist()
    
    cores_barras = []
    maior_grau = max(graus)
    
    for grau in graus:
        if grau == maior_grau:
            cores_barras.append(COR_DESTAQUE) 
        else:
            cores_barras.append('#6c63ff') 
            
    fig, ax = plt.subplots(figsize=(10, 6))
    aplicar_estilo_escuro(fig, ax)
    
    ax.barh(aeroportos, graus, color=cores_barras, edgecolor=COR_FUNDO)
    
    ax.set_title('Top 10 Aeroportos Mais Conectados', fontsize=12, fontweight='bold')
    ax.set_xlabel('Número de conexões diretas (grau)', fontsize=10)
    ax.set_ylabel('Aeroporto (código IATA)', fontsize=10)
    
    for i in range(len(aeroportos)):
        cor_num = COR_DESTAQUE if graus[i] == maior_grau else COR_TEXTO
        ax.text(graus[i] + 0.3, i, str(graus[i]), va='center', color=cor_num, fontsize=9, fontweight='bold')
        
    # Adiciona a legenda organizada no canto da tela
    legenda_destaque = mpatches.Patch(color=COR_DESTAQUE, label='Maior hub da malha aérea')
    ax.legend(handles=[legenda_destaque], loc='lower right', facecolor=COR_PLANO, edgecolor=COR_GRADE, labelcolor=COR_TEXTO)
        
    ax.set_xlim(0, max(graus) + 2)
    fig.tight_layout()
    
    caminho_salvar = os.path.join(pasta_saida, 'vis1_ranking_hubs.png')
    fig.savefig(caminho_salvar, format='png', dpi=150, facecolor=COR_FUNDO)
    plt.close(fig)


def gerar_vis2_distribuicao_graus(caminho_graus, pasta_saida):
    tabela = pd.read_csv(caminho_graus, encoding='utf-8')
    graus = tabela['grau'].tolist()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    aplicar_estilo_escuro(fig, ax)
    
    contagem, bordas, barras = ax.hist(graus, bins=10, edgecolor=COR_FUNDO)
    
    maior_frequencia = max(contagem)
    
    for barra in barras:
        if barra.get_height() == maior_frequencia:
            barra.set_facecolor(COR_DESTAQUE)
            barra.set_alpha(1.0)
        else:
            barra.set_facecolor('#00c2a8')
            barra.set_alpha(0.6) 
            
    ax.set_title('Distribuição do Número de Conexões', fontsize=12, fontweight='bold')
    ax.set_xlabel('Número de conexões diretas (grau)', fontsize=10)
    ax.set_ylabel('Quantidade de aeroportos', fontsize=10)
    
    # Adiciona a legenda organizada
    legenda_destaque = mpatches.Patch(color=COR_DESTAQUE, label='Maior concentração da rede')
    ax.legend(handles=[legenda_destaque], loc='upper right', facecolor=COR_PLANO, edgecolor=COR_GRADE, labelcolor=COR_TEXTO)
    
    fig.tight_layout()
    
    caminho_salvar = os.path.join(pasta_saida, 'vis2_distribuicao_graus.png')
    fig.savefig(caminho_salvar, format='png', dpi=150, facecolor=COR_FUNDO)
    plt.close(fig)


def gerar_vis3_comparacao_regioes(caminho_regioes, pasta_saida):
    with open(caminho_regioes, 'r', encoding='utf-8') as arquivo:
        dados = json.load(arquivo)
        
    regioes = []
    ordem = []
    tamanho = []
    
    for regiao, valores in dados.items():
        regioes.append(regiao)
        ordem.append(valores['ordem'])
        tamanho.append(valores['tamanho'])
        
    posicoes_x = list(range(len(regioes)))
    pos_azul = [x - 0.2 for x in posicoes_x]
    pos_laranja = [x + 0.2 for x in posicoes_x]
    
    maior_tamanho = max(tamanho)
    cores_tamanho = []
    
    for val in tamanho:
        if val == maior_tamanho:
            cores_tamanho.append(COR_DESTAQUE)
        else:
            cores_tamanho.append('#00c2a8')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    aplicar_estilo_escuro(fig, ax)
    
    ax.bar(pos_azul, ordem, width=0.4, label='Aeroportos (ordem)', color='#e84393', edgecolor=COR_FUNDO)
    ax.bar(pos_laranja, tamanho, width=0.4, label='Voos internos (tamanho)', color=cores_tamanho, edgecolor=COR_FUNDO)
    
    ax.set_title('Infraestrutura Aérea por Região', fontsize=12, fontweight='bold')
    ax.set_xlabel('Região do Brasil', fontsize=10)
    ax.set_ylabel('Quantidade', fontsize=10)
    
    ax.set_xticks(posicoes_x)
    ax.set_xticklabels(regioes)
    
    for i in range(len(regioes)):
        ax.text(pos_azul[i], ordem[i] + 0.5, str(ordem[i]), ha='center', color=COR_TEXTO, fontsize=9)
        
        cor_num = COR_DESTAQUE if tamanho[i] == maior_tamanho else COR_TEXTO
        peso_fonte = 'bold' if tamanho[i] == maior_tamanho else 'normal'
        ax.text(pos_laranja[i], tamanho[i] + 0.5, str(tamanho[i]), ha='center', color=cor_num, fontsize=9, fontweight=peso_fonte)
        
    # Organiza a legenda existente e adiciona a nossa customizada de destaque
    handles, labels = ax.get_legend_handles_labels()
    legenda_destaque = mpatches.Patch(color=COR_DESTAQUE, label='Maior malha interna')
    handles.append(legenda_destaque)
    
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 1.0), ncol=3, facecolor=COR_PLANO, edgecolor=COR_GRADE, labelcolor=COR_TEXTO)
        
    ax.set_ylim(0, max(max(ordem), max(tamanho)) + 5)
    fig.tight_layout()
    
    caminho_salvar = os.path.join(pasta_saida, 'vis3_comparacao_regioes.png')
    fig.savefig(caminho_salvar, format='png', dpi=150, facecolor=COR_FUNDO)
    plt.close(fig)



if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(__file__))
    
    caminho_graus = os.path.join(base_path, 'out', 'graus.csv')
    caminho_regioes = os.path.join(base_path, 'out', 'regioes.json')
    caminho_adj = os.path.join(base_path, 'data', 'adjacencias_aeroportos.csv')
    pasta_saida = os.path.join(base_path, 'out')
    
    gerar_vis1_ranking_hubs(caminho_graus, pasta_saida)
    gerar_vis2_distribuicao_graus(caminho_graus, pasta_saida)
    gerar_vis3_comparacao_regioes(caminho_regioes, pasta_saida)