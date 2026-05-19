# Rede de Aeroportos do Brasil + Comparação de Algoritmos

Projeto final de Teoria dos Grafos — modelagem da malha aérea brasileira (Parte 1) e comparação de algoritmos em dataset maior do Spotify (Parte 2).

## Requisitos

- Python 3.11+
- Instalar dependências:

```bash
pip install -r requirements.txt
```

## Estrutura do projeto

```
projeto-grafos/
├── data/
│   ├── aeroportos_data.csv          # dados dos aeroportos
│   ├── adjacencias_aeroportos.csv   # arestas construídas pelo grupo
│   ├── rotas.csv                    # pares origem-destino para Dijkstra
│   └── dataset_parte2/
│       └── dataset.csv              # Spotify Tracks Dataset (Kaggle)
├── out/                             # saídas geradas (.json/.html/.png)
├── src/
│   ├── solve.py                     # pipeline Parte 1
│   ├── analise.py                   # visualizações Parte 1
│   ├── analise_etapa10.py           # análise AVD Parte 1
│   ├── analise_parte2.py            # pipeline Parte 2
│   ├── viz.py                       # grafo interativo e árvores de percurso
│   └── graphs/
│       ├── graph.py                 # estrutura: lista de adjacência
│       ├── algorithms.py            # BFS, DFS, Dijkstra, Bellman-Ford
│       └── io.py                    # leitura/validação de CSVs
└── tests/
    ├── test_bfs.py
    ├── test_dfs.py
    ├── test_dijkstra.py
    └── test_bellman_ford.py
```

## Parte 1 — Grafo de Aeroportos do Brasil

Executa todas as etapas: métricas globais, rotas com Dijkstra e visualizações.

```bash
python -m src.solve
```

Gera visualizações analíticas (AVD):

```bash
python -m src.analise
python -m src.analise_etapa10
```

Gera o grafo interativo e árvores de percurso:

```bash
python -m src.viz
```

### Saídas geradas em `out/`

| Arquivo | Conteúdo |
|---|---|
| `global.json` | Ordem, tamanho e densidade do grafo completo |
| `regioes.json` | Métricas por região (Norte, Nordeste, etc.) |
| `ego_aeroportos.csv` | Grau, ordem, tamanho e densidade ego por aeroporto |
| `graus.csv` | Ranking de graus |
| `distancias_rotas.csv` | Caminhos mínimos (Dijkstra) para os pares em `rotas.csv` |
| `arvore_percurso_*.html` | Árvore de caminho interativa para cada rota |
| `grafo_interativo.html` | Grafo completo interativo com busca e destaque de caminhos |
| `vis1_ranking_hubs.png` | Top 10 aeroportos mais conectados |
| `vis2_distribuicao_graus.png` | Distribuição de graus |
| `vis3_comparacao_regioes.png` | Comparação de métricas por região |
| `vis4_subgrafo_hubs.html` | Subgrafo dos maiores hubs |
| `vis_exp1_*`, `vis_exp2_*` | Visualizações exploratórias |
| `vis_expl1_*`, `vis_expl2_*` | Visualizações explanatórias |

## Parte 2 — Dataset Spotify + Comparação de Algoritmos

**Dataset:** [Spotify Tracks Dataset (Kaggle)](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)  
**Nós:** faixas musicais | **Arestas:** K vizinhos mais próximos por distância euclidiana de features de áudio | **Restrição:** não é dataset de malha aérea

```bash
python -m src.analise_parte2
```

O script:
1. Amostra 2.000 faixas de forma estratificada por gênero
2. Constrói um grafo KNN dirigido (~57.000 arestas, K=30)
3. Executa e mede o tempo de BFS, DFS, Dijkstra e Bellman-Ford
4. Demonstra Bellman-Ford com pesos negativos (DAG, sem ciclo negativo)
5. Demonstra detecção de ciclo negativo pelo Bellman-Ford
6. Gera 4 visualizações e o relatório `out/parte2_report.json`

### Saídas geradas em `out/`

| Arquivo | Conteúdo |
|---|---|
| `parte2_report.json` | Métricas do dataset e tempos de execução de cada algoritmo |
| `p2_vis1_distribuicao_graus.png` | Histograma de graus do grafo Spotify |
| `p2_vis2_tempo_algoritmos.png` | Comparação de tempo médio por algoritmo |
| `p2_vis3_heatmap_distancias.png` | Heatmap de distâncias entre 20 faixas |
| `p2_vis4_bfs_camadas.png` | Distribuição de nós por camada (BFS) |

## Testes

```bash
python -m pytest tests/ -v
```

Cobertura mínima exigida:

- **BFS:** níveis corretos, ordem de largura, nó isolado
- **DFS:** detecção de ciclo, classificação de arestas (tree/back/forward/cross)
- **Dijkstra:** caminhos corretos, rejeita pesos negativos, nó inalcançável
- **Bellman-Ford:** pesos negativos sem ciclo, detecção de ciclo negativo, equivalência com Dijkstra

## Algoritmos implementados

Todos implementados do zero em `src/graphs/algorithms.py` (sem uso de networkx, igraph ou similares).

| Algoritmo | Complexidade | Pesos negativos |
|---|---|---|
| BFS | O(V + E) | não se aplica |
| DFS | O(V + E) | não se aplica |
| Dijkstra | O((V + E) log V) | não suporta |
| Bellman-Ford | O(V · E) | suporta + detecta ciclo negativo |
