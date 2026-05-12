import pandas as pd
import os
import sys
import json
from collections import OrderedDict

sys.path.append(os.path.join(os.path.dirname(__file__)))

from graphs.algorithms import dijkstra
from viz import gerar_html_do_caminho

class GrafoAeroportos:
    def __init__(self):
        self.adj = {}
        self.nos_ordenados = []

    def adicionar_aresta(self, u, v, peso):
        if u not in self.adj: self.adj[u] = []
        if v not in self.adj: self.adj[v] = []
        self.adj[u].append((v, peso))
        self.adj[v].append((u, peso)) 
        if u not in self.nos_ordenados: self.nos_ordenados.append(u)
        if v not in self.nos_ordenados: self.nos_ordenados.append(v)

    def obter_todos_nos(self):
        return self.nos_ordenados

    def obter_vizinhos_com_peso(self, u):
        return self.adj.get(u, [])
        
    def obter_vizinhos_simples(self, u):
        return [vizinho for vizinho, _ in self.adj.get(u, [])]

def calcular_densidade(ordem, tamanho):
    if ordem < 2: return 0.0
    return (2 * tamanho) / (ordem * (ordem - 1))

def resolver_etapas_3_e_4(grafo, caminho_aeroportos_data, pasta_saida):
    print("\n--- Processando Etapas 3 e 4 (Metricas e Rankings) ---")
    ordem_global = len(grafo.obter_todos_nos())
    tamanho_global = sum(len(grafo.obter_vizinhos_simples(no)) for no in grafo.obter_todos_nos()) // 2
    densidade_global = calcular_densidade(ordem_global, tamanho_global)
    
    with open(os.path.join(pasta_saida, 'global.json'), 'w', encoding='utf-8') as f:
        json.dump({"ordem": ordem_global, "tamanho": tamanho_global, "densidade": round(densidade_global, 4)}, f, indent=4)

    try:
        df_aero = pd.read_csv(caminho_aeroportos_data, encoding='utf-8')
        col_iata = df_aero.columns[0]
        col_regiao = df_aero.columns[2]
        mapa_regioes = dict(zip(df_aero[col_iata], df_aero[col_regiao]))
        ordem_das_regioes = list(OrderedDict.fromkeys(df_aero[col_regiao]))
        ordem_iata_original = list(df_aero[col_iata])
        
        regioes_info = {}
        for regiao in ordem_das_regioes:
            nos_da_regiao = [no for no in grafo.obter_todos_nos() if mapa_regioes.get(no) == regiao]
            ordem_reg = len(nos_da_regiao)
            tamanho_reg = 0
            for no in nos_da_regiao:
                vizinhos = grafo.obter_vizinhos_simples(no)
                tamanho_reg += sum(1 for v in vizinhos if v in nos_da_regiao)
            tamanho_reg //= 2
            regioes_info[regiao] = {"ordem": ordem_reg, "tamanho": tamanho_reg, "densidade": round(calcular_densidade(ordem_reg, tamanho_reg), 4)}
            
        with open(os.path.join(pasta_saida, 'regioes.json'), 'w', encoding='utf-8') as f:
            json.dump(regioes_info, f, indent=4)

        ego_dados = []
        graus_dados = []
        for no in ordem_iata_original:
            if no in grafo.obter_todos_nos():
                vizinhos = grafo.obter_vizinhos_simples(no)
                grau = len(vizinhos)
                graus_dados.append({"aeroporto": no, "grau": grau})
                
                ordem_ego = grau + 1
                tamanho_ego = grau 
                densidade_ego = calcular_densidade(ordem_ego, tamanho_ego)
                
                ego_dados.append({
                    "aeroporto": no,
                    "grau": grau,
                    "ordem_ego": ordem_ego,
                    "tamanho_ego": tamanho_ego,
                    "densidade_ego": round(densidade_ego, 3)
                })
        
        pd.DataFrame(ego_dados).to_csv(os.path.join(pasta_saida, 'ego_aeroportos.csv'), index=False, encoding='utf-8')
        pd.DataFrame(graus_dados).to_csv(os.path.join(pasta_saida, 'graus.csv'), index=False, encoding='utf-8')
        print("OK: Metricas salvas.")
    except Exception as e:
        print(f"Erro: {e}")

def resolver_etapa_6(grafo, caminho_rotas, pasta_saida):
    print("\n--- Processando Etapa 6 (Rotas com Dijkstra) ---")
    try:
        df_rotas = pd.read_csv(caminho_rotas, encoding='utf-8')
        resultados = []
        
        for _, linha in df_rotas.iterrows():
            origem = str(linha['origem']).strip()
            destino = str(linha['destino']).strip()
            custo, caminho = dijkstra(grafo, origem, destino)
                
            resultados.append({
                'origem': origem, 
                'destino': destino, 
                'custo': custo if custo != float('inf') else "Inalcancavel", 
                'caminho': " -> ".join(caminho) if caminho else "Nenhum"
            })
            
        pd.DataFrame(resultados).to_csv(os.path.join(pasta_saida, 'distancias_rotas.csv'), index=False, encoding='utf-8')
        print("OK: distancias_rotas.csv gerado.")
    except Exception as e:
        print(f"Erro: {e}")

def resolver_etapa_7(grafo, caminho_rotas, pasta_saida):
    print("\nprocessando etapa 7")

    try:
        df_rotas = pd.read_csv(caminho_rotas, encoding='utf-8')
        
        for _, linha in df_rotas.iterrows():
            origem = str(linha['origem']).strip()
            destino = str(linha['destino']).strip()
            
            custo, trajeto = dijkstra(grafo, origem, destino)
            
            if trajeto and custo != float('inf'):
                gerar_html_do_caminho(grafo, trajeto, origem, destino, pasta_saida)
                
        print("OK: Arquivos HTML individuais gerados para cada rota na pasta out/.")
    except Exception as e:
        print(f"Erro na Etapa 7: {e}")

def main():
    base_path = os.path.dirname(os.path.dirname(__file__))
    caminho_adj = os.path.join(base_path, 'data', 'adjacencias_aeroportos.csv')
    caminho_rotas = os.path.join(base_path, 'data', 'rotas.csv')
    caminho_aeroportos_data = os.path.join(base_path, 'data', 'aeroportos_data.csv')
    pasta_saida = os.path.join(base_path, 'out')
    
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    try:
        df_adj = pd.read_csv(caminho_adj, encoding='utf-8')
        grafo = GrafoAeroportos()
        for _, linha in df_adj.iterrows():
            grafo.adicionar_aresta(str(linha['origem']).strip(), str(linha['destino']).strip(), float(linha['peso']))
            
        resolver_etapas_3_e_4(grafo, caminho_aeroportos_data, pasta_saida)
        resolver_etapa_6(grafo, caminho_rotas, pasta_saida)
        resolver_etapa_7(grafo, caminho_rotas, pasta_saida)
        
        print("\n--- Processamento Finalizado com Sucesso ---")
    except Exception as e:
        print(f"Erro no processamento principal: {e}")

if __name__ == "__main__":
    main()