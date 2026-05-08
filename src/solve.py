import os
import sys
import json
import pandas as pd
from collections import OrderedDict
from graphs.io import carregarCsv
from graphs.algorithms import dijkstra
sys.path.append(os.path.join(os.path.dirname(__file__)))


class GrafoAeroportos:
    def __init__(self):
        self.adj = {}
        self.listaVertices = []

    def adicionar_aresta(self, vertice1, vertice2, peso):
        if vertice1 not in self.adj:
            self.adj[vertice1] = []
        if vertice2 not in self.adj:
            self.adj[vertice2] = []
        self.adj[vertice1].append((vertice2, peso))
        self.adj[vertice2].append((vertice1, peso)) 
        if vertice1 not in self.listaVertices: 
            self.listaVertices.append(vertice1)
        if vertice2 not in self.listaVertices: 
            self.listaVertices.append(vertice2)

    def listaAeroportos(self):
        return self.listaVertices

    def listaVizinhoPesos(self, vertice):
        return self.adj.get(vertice, [])
        
    def listaVizinhos(self, vertice):
        return [vizinho for vizinho, _ in self.adj.get(vertice, [])]

def densidade(ordem, tamanho):
    if ordem < 2: 
        return 0.0
    return (2 * tamanho) / (ordem * (ordem - 1))

def etapa3(grafo, caminhoDadosAeroportos, out):
    ordemGrafo = len(grafo.listaAeroportos())
    somaGraus = 0
    for vertice in grafo.listaAeroportos():
        vizinhos = grafo.listaVizinhos(vertice)
        somaGraus = somaGraus + len(vizinhos)
    
    tamanhoGrafo = somaGraus // 2
    densidadeGrafo = densidade(ordemGrafo, tamanhoGrafo)
    
    with open(os.path.join(out, 'global.json'), 'w', encoding='utf-8') as f:
        json.dump({"ordem": ordemGrafo, "tamanho": tamanhoGrafo, "densidade": round(densidadeGrafo, 4)}, f, indent=4)
        
    dfAeroportos = carregarCsv(caminhoDadosAeroportos)
    mapaRegioes = dict(zip(dfAeroportos['iata'], dfAeroportos['regiao']))
    regioesInfo = {}

    listaRegioes = dfAeroportos['regiao'].unique()

    for regiao in listaRegioes:
        verticesRegiao = []
        for iata in grafo.listaAeroportos():
            if mapaRegioes.get(iata) == regiao:
                verticesRegiao.append(iata)
        
        ordemRegiao = len(verticesRegiao)
        tamanhoRegiao = 0
        for i in verticesRegiao:
            vizinhos = grafo.listaVizinhos(i)
            for v in vizinhos:
                if v in verticesRegiao:
                    tamanhoRegiao = tamanhoRegiao + 1
        
        tamanhoRegiao = tamanhoRegiao // 2
        regioesInfo[regiao] = {
            "ordem": ordemRegiao, 
            "tamanho": tamanhoRegiao, 
            "densidade": round(densidade(ordemRegiao, tamanhoRegiao), 4)
        }
    with open(os.path.join(out, 'regioes.json'), 'w', encoding='utf-8') as f:
        json.dump(regioesInfo, f, indent=4)
        
def etapa4(grafo, caminhoDadosAeroportos, out):
    dfAeroportos = carregarCsv(caminhoDadosAeroportos)
    dadosEgo = []
    dadosGraus = []

    for iata in dfAeroportos['iata']:
        if iata in grafo.listaAeroportos():
            vizinhos = grafo.listaVizinhos(iata)
            valorGrau = len(vizinhos)
            dadosGraus.append({
                "aeroporto": iata, 
                "grau": valorGrau
            })
            ordemEgo = valorGrau + 1
            tamanhoEgo = valorGrau 
            densidadeEgo = densidade(ordemEgo, tamanhoEgo)
            
            dadosEgo.append({
                "aeroporto": iata,
                "grau": valorGrau,
                "ordem_ego": ordemEgo,
                "tamanho_ego": tamanhoEgo,
                "densidade_ego": round(densidadeEgo, 3)
            })
    pd.DataFrame(dadosEgo).to_csv(os.path.join(out, 'ego_aeroportos.csv'), index=False)
    pd.DataFrame(dadosGraus).to_csv(os.path.join(out, 'graus.csv'), index=False)

def etapa6(grafo, caminhoRotas, out):
    try:
        dfRotas = carregarCsv(caminhoRotas)
        resultados = []
        
        for _, linha in dfRotas.iterrows():
            origem = str(linha['origem']).strip()
            destino = str(linha['destino']).strip()
            custo, caminho = dijkstra(grafo, origem, destino)
                
            resultados.append({
                'origem': origem, 
                'destino': destino, 
                'custo': custo if custo != float('inf') else "Inalcancavel", 
                'caminho': " -> ".join(caminho) if caminho else "Nenhum"
            })
        pd.DataFrame(resultados).to_csv(os.path.join(out, 'distancias_rotas.csv'), index=False, encoding='utf-8')
    except Exception as e:
        print(f"Erro: {e}")

def main():
    diretorioAtual = os.path.dirname(os.path.abspath(__file__))
    raiz = os.path.dirname(diretorioAtual)
    
    caminhoAdjacencias = os.path.join(raiz, 'data', 'adjacencias_aeroportos.csv')
    caminhoRotas = os.path.join(raiz, 'data', 'rotas.csv')
    caminhoDadosAeroportos = os.path.join(raiz, 'data', 'aeroportos_data.csv')
    out = os.path.join(raiz, 'out')
    
    if not os.path.exists(out):
        os.makedirs(out)

    try:
        df_adj = carregarCsv(caminhoAdjacencias)
        grafo = GrafoAeroportos()
        for _, linha in df_adj.iterrows():
            grafo.adicionar_aresta(str(linha['origem']).strip(), str(linha['destino']).strip(), float(linha['peso']))
            
        etapa3(grafo, caminhoDadosAeroportos, out)
        etapa4(grafo,caminhoDadosAeroportos, out)
        etapa6(grafo, caminhoRotas, out)
        
    except Exception as e:
        print(f"\nFalha ao iniciar projeto: {e}")

if __name__ == "__main__":
    main()