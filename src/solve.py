import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from graphs.algorithms import dijkstra

class GrafoAeroportos:
    def __init__(self):
        self.adj = {}
        self.nos = set()

    def adicionar_aresta(self, u, v, peso):
        if u not in self.adj: self.adj[u] = []
        if v not in self.adj: self.adj[v] = []
        self.adj[u].append((v, peso))
        self.adj[v].append((u, peso)) 
        self.nos.add(u)
        self.nos.add(v)

    def obter_todos_nos(self):
        return list(self.nos)

    def obter_vizinhos_com_peso(self, u):
        return self.adj.get(u, [])

def resolver_etapa_6():
    base_path = os.path.dirname(os.path.dirname(__file__))
    caminho_adj = os.path.join(base_path, 'data', 'adjacencias_aeroportos.csv')
    caminho_rotas = os.path.join(base_path, 'data', 'rotas.csv')
    pasta_saida = os.path.join(base_path, 'out')
    
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    print(f"Lendo dados de: {caminho_adj}")
    
    try:
        df_adj = pd.read_csv(caminho_adj)
        df_rotas = pd.read_csv(caminho_rotas)
        
        grafo = GrafoAeroportos()
        for _, linha in df_adj.iterrows():
            grafo.adicionar_aresta(str(linha['origem']), str(linha['destino']), float(linha['peso']))
            
        resultados = []
        for _, linha in df_rotas.iterrows():
            origem = str(linha['origem'])
            destino = str(linha['destino'])
            
            custo, caminho = dijkstra(grafo, origem, destino)
            
            resultados.append({
                'origem': origem,
                'destino': destino,
                'custo': custo if custo != float('inf') else "Inalcançável",
                'caminho': " -> ".join(caminho) if caminho else "Nenhum"
            })
            
        df_final = pd.DataFrame(resultados)
        output_file = os.path.join(pasta_saida, 'distancias_rotas.csv')
        df_final.to_csv(output_file, index=False)
        print(f"\n✓ Sucesso! Arquivo gerado em: {output_file}")
        print(df_final[['origem', 'destino', 'custo']].to_string(index=False))

    except Exception as e:
        print(f"Erro ao processar: {e}")

if __name__ == "__main__":
    resolver_etapa_6()