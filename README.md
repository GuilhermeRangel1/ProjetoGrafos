# DataGraph

DataGraph - modelagem da malha aerea brasileira (Parte 1) e comparacao de algoritmos em dataset maior do Spotify (Parte 2), com interface web interativa unificada.

## Requisitos

- Python 3.11+
- Node.js 18+

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
├── spotify-graph/                   # app React da interface web
├── src/
│   ├── solve.py                     # pipeline Parte 1
│   ├── analise.py                   # visualizações Parte 1
│   ├── analise_etapa10.py           # análise AVD Parte 1
│   ├── analise_parte2.py            # pipeline Parte 2
│   ├── viz.py                       # grafo interativo e árvores de percurso
│   ├── api.py                       # API Flask para o app web (Parte 2)
│   ├── gerador_playlists.py         # geração de playlists via BFS/DFS
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

## Interface web interativa

A interface unifica os dois grafos em uma página de entrada com navegação entre eles.

### Rodando com Docker

```bash
docker compose up --build
```

Acesse `http://localhost:5173`. O Compose sobe a API Flask em `http://localhost:5000` e o frontend Vite em `http://localhost:5173`.

**Terminal 1 — backend (necessário para a Parte 2):**

```bash
python src/api.py
```

**Terminal 2 — frontend:**

```bash
cd spotify-graph
npm install   # apenas na primeira vez
npm run dev
```

Acesse `http://localhost:5173`. A página inicial permite escolher entre o grafo de aeroportos e o grafo do Spotify.

## Parte 1 — Grafo de Aeroportos do Brasil

Executa todas as etapas: métricas globais, rotas com Dijkstra e visualizações.

```bash
python -m src.solve
```

Gera visualizações analíticas:

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
| `regioes.json` | Métricas por região |
| `ego_aeroportos.csv` | Grau, ordem, tamanho e densidade ego por aeroporto |
| `graus.csv` | Ranking de graus |
| `distancias_rotas.csv` | Caminhos mínimos (Dijkstra) para os pares em `rotas.csv` |
| `arvore_percurso_*.html` | Árvore de caminho interativa para cada rota |
| `grafo_interativo.html` | Grafo completo interativo com busca e destaque de caminhos |
| `vis1_ranking_hubs.png` | Top 10 aeroportos mais conectados |
| `vis2_distribuicao_graus.png` | Distribuição de graus |
| `vis3_comparacao_regioes.png` | Comparação de métricas por região |
| `vis4_subgrafo_hubs.html` | Subgrafo dos maiores hubs |

## Parte 2 — Dataset Spotify + Comparação de Algoritmos

**Dataset:** [Spotify Tracks Dataset (Kaggle)](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)  
**Nós:** faixas musicais | **Arestas:** K vizinhos mais próximos por distância euclidiana de features de áudio

```bash
python -m src.analise_parte2
```

O script:
1. Amostra 2.000 faixas de forma estratificada por gênero
2. Constrói um grafo KNN dirigido (~57.000 arestas, K=30)
3. Executa e mede o tempo de BFS, DFS, Dijkstra e Bellman-Ford
4. Demonstra Bellman-Ford com pesos negativos e detecção de ciclo negativo
5. Gera 4 visualizações e o relatório `out/parte2_report.json`

Para gerar playlists via terminal:

```bash
python -m src.gerador_playlists
```

### Saídas geradas em `out/`

| Arquivo | Conteúdo |
|---|---|
| `parte2_report.json` | Métricas do dataset e tempos de execução por algoritmo |
| `p2_vis1_distribuicao_graus.png` | Histograma de graus do grafo Spotify |
| `p2_vis2_tempo_algoritmos.png` | Comparação de tempo médio por algoritmo |
| `p2_vis3_heatmap_distancias.png` | Heatmap de distâncias entre 20 faixas |
| `p2_vis4_bfs_camadas.png` | Distribuição de nós por camada (BFS) |
| `playlists_geradas.txt` | Playlists geradas pelo `gerador_playlists.py` |

## Testes

```bash
python -m pytest tests/ -v
```

Cobertura mínima:

- **BFS:** níveis corretos, ordem de largura, nó isolado
- **DFS:** detecção de ciclo, classificação de arestas (tree/back/forward/cross)
- **Dijkstra:** caminhos corretos, rejeita pesos negativos, nó inalcançável
- **Bellman-Ford:** pesos negativos sem ciclo, detecção de ciclo negativo, equivalência com Dijkstra

## Algoritmos implementados

Todos implementados do zero em `src/graphs/algorithms.py`, sem uso de networkx, igraph ou similares.

| Algoritmo | Complexidade | Pesos negativos |
|---|---|---|
| BFS | O(V + E) | não se aplica |
| DFS | O(V + E) | não se aplica |
| Dijkstra | O((V + E) log V) | não suporta |
| Bellman-Ford | O(V · E) | suporta + detecta ciclo negativo |
