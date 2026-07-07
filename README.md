# DataGraph

DataGraph é um projeto de grafos com duas experiências interativas:

- **AeroGraph:** análise da malha aérea brasileira a partir de aeroportos, rotas, centralidade, caminhos mínimos e insights operacionais.
- **SoundGraph:** exploração de um dataset do Spotify com grafo artista-gênero-música, filtros, buscas, visualização em rede e playlists geradas por algoritmos.

O frontend unifica os dois módulos em uma interface web. A Parte 1 é exibida por um HTML interativo gerado em Python; a Parte 2 usa React, Vite e uma visualização force-directed em canvas.

## Requisitos

- Python 3.11+
- Node.js 18+
- Docker e Docker Compose, opcional

Instale as dependências Python:

```bash
pip install -r requirements.txt
```

Instale as dependências do frontend:

```bash
cd spotify-graph
npm install
```

## Como Rodar

### Com Docker

```bash
docker compose up --build
```

Acesse:

- Frontend: `http://localhost:5173`
- API Flask: `http://localhost:5000`

### Sem Docker

Terminal 1, API da Parte 2:

```bash
python src/api.py
```

Terminal 2, frontend:

```bash
cd spotify-graph
npm run dev
```

Acesse `http://localhost:5173`.

## Estrutura

```text
data/
  aeroportos_data.csv                 # base manual original de aeroportos
  adjacencias_aeroportos.csv          # conexões manuais originais
  aeroportos_data_real.csv            # aeroportos brasileiros importados de fontes públicas
  adjacencias_aeroportos_real.csv     # conexões reais/proxy entre aeroportos brasileiros
  aeroportos_fontes_real.json         # fontes e metadados da importação
  rotas.csv                           # pares origem-destino usados no Dijkstra
  dataset_parte2/dataset.csv          # Spotify Tracks Dataset

src/
  solve.py                            # pipeline de métricas e rotas do AeroGraph
  viz.py                              # HTML interativo do AeroGraph
  import_aeroportos_reais.py          # importador OurAirports/OpenFlights
  auditar_aeroportos_reais.py         # auditoria de coerência da malha aérea
  analise.py                          # gráficos estáticos da Parte 1
  analise_etapa10.py                  # análises complementares da Parte 1
  analise_parte2.py                   # análise offline do SoundGraph
  api.py                              # API Flask para playlists BFS/DFS
  gerador_playlists.py                # playlists via terminal
  graphs/
    graph.py                          # estrutura de grafo
    algorithms.py                     # BFS, DFS, Dijkstra, Bellman-Ford
    io.py                             # leitura e validação de CSV

spotify-graph/
  src/                                # aplicação React
  public/grafo_interativo.html        # HTML atual do AeroGraph usado no iframe

out/                                  # artefatos gerados
tests/                                # testes unitários dos algoritmos
```

## AeroGraph

O AeroGraph modela a malha aérea brasileira como um grafo não direcionado:

- **Nós:** aeroportos com código IATA.
- **Arestas:** conexões entre aeroportos.
- **Peso:** distância aproximada em quilômetros, calculada por Haversine.
- **Metadados:** região, cidade, UF, tipo de conexão, frequência estimada e fonte.

### Dados Reais/Proxy

O importador usa fontes públicas:

- [OurAirports](https://davidmegginson.github.io/ourairports-data/airports.csv), para cadastro, coordenadas e metadados dos aeroportos.
- [OpenFlights](https://github.com/jpatokal/openflights), para rotas públicas/históricas usadas como proxy de conexões regulares.

```bash
python -m src.import_aeroportos_reais
```

Quando os arquivos `data/*_real.*` existem, `solve.py` e `viz.py` usam automaticamente essa malha. Se eles forem removidos, o projeto volta para os CSVs manuais originais.

### Malha Ativa

A base realista contém todos os aeroportos brasileiros com IATA encontrados nas fontes. Para evitar uma visualização artificialmente poluída, aeroportos cadastrados sem nenhuma conexão registrada são descartados da visualização e das métricas ativas.

Assim, a base completa continua em `data/aeroportos_data_real.csv`, mas o grafo exibido no AeroGraph considera apenas aeroportos com grau maior que zero.

### Gerar Métricas, Rotas e Visualização

```bash
python -m src.solve
python -m src.viz
```

Depois de gerar o HTML, copie-o para o frontend:

```powershell
Copy-Item -LiteralPath out\grafo_interativo.html -Destination spotify-graph\public\grafo_interativo.html -Force
```

### Auditar a Coerência dos Dados

```bash
python -m src.auditar_aeroportos_reais
```

A auditoria verifica endpoints inexistentes, auto-laços, duplicatas não direcionadas, pesos inválidos, distâncias divergentes e aeroportos descartados por grau zero.

### Saídas Principais do AeroGraph

| Arquivo | Conteúdo |
|---|---|
| `out/global.json` | Ordem, tamanho e densidade da malha ativa |
| `out/regioes.json` | Ordem, tamanho e densidade por região |
| `out/ego_aeroportos.csv` | Grau e densidade ego por aeroporto |
| `out/graus.csv` | Ranking de aeroportos por grau |
| `out/distancias_rotas.csv` | Caminhos mínimos calculados por Dijkstra |
| `out/arvore_percurso_*.html` | Árvores/caminhos interativos para rotas específicas |
| `out/grafo_interativo.html` | Experiência principal do AeroGraph |

Na interface, o AeroGraph inclui mapa interativo, filtros, busca de rota mínima, métricas ego, gráficos analíticos e uma seção de insights sobre concentração, integração regional, risco operacional e decisões recomendadas.

## SoundGraph

O SoundGraph explora o Spotify Tracks Dataset como uma rede musical interativa:

- **Nós de artista:** artistas conectados aos gêneros e faixas.
- **Nós de gênero:** categorias musicais traduzidas para português na interface.
- **Nós de música:** exibidos opcionalmente para manter desempenho.
- **Arestas:** relações artista-gênero e artista-música.

O frontend carrega o dataset diretamente em `spotify-graph/public/dataset.csv`, processa os dados no navegador e limita a quantidade renderizada conforme os filtros para manter a visualização fluida.

### Análise Offline da Parte 2

```bash
python -m src.analise_parte2
```

Esse script cria uma amostra estratificada do dataset, monta um grafo KNN com features de áudio normalizadas e executa BFS, DFS, Dijkstra e Bellman-Ford para comparação dos algoritmos.

### Playlists Via Terminal

```bash
python -m src.gerador_playlists
```

### Saídas Principais do SoundGraph

| Arquivo | Conteúdo |
|---|---|
| `out/parte2_report.json` | Métricas do dataset e tempos dos algoritmos |
| `out/p2_vis1_distribuicao_graus.png` | Distribuição de graus do grafo musical |
| `out/p2_vis2_tempo_algoritmos.png` | Comparação de tempo médio por algoritmo |
| `out/p2_vis3_heatmap_distancias.png` | Heatmap de distâncias entre faixas |
| `out/p2_vis4_bfs_camadas.png` | Distribuição de nós por camada BFS |
| `out/playlists_geradas.txt` | Playlists geradas via BFS/DFS |

Na interface, o SoundGraph inclui filtros por artista, música, popularidade, gênero, quantidade máxima de artistas, animação de caminhos, painel de detalhes e geração de playlists automáticas.

## Testes

```bash
python -m pytest tests/ -v
```

Cobertura principal:

- **BFS:** ordem em largura, níveis e nós isolados.
- **DFS:** ordem de visita, ciclos e classificação de arestas.
- **Dijkstra:** caminhos mínimos, pesos negativos rejeitados e nós inalcançáveis.
- **Bellman-Ford:** pesos negativos, detecção de ciclo negativo e equivalência com Dijkstra quando aplicável.

## Build do Frontend

```bash
cd spotify-graph
npm run build
```

## Algoritmos Implementados

Todos os algoritmos centrais estão implementados em `src/graphs/algorithms.py`.

| Algoritmo | Complexidade | Observação |
|---|---:|---|
| BFS | O(V + E) | Percurso em largura e camadas |
| DFS | O(V + E) | Percurso em profundidade e classificação de arestas |
| Dijkstra | O((V + E) log V) | Caminho mínimo com pesos não negativos |
| Bellman-Ford | O(V * E) | Suporta pesos negativos e detecta ciclo negativo |

## Observações Metodológicas

- As rotas reais do AeroGraph são uma aproximação baseada em dados públicos/históricos, não uma consulta em tempo real a malhas comerciais atuais.
- A remoção dos aeroportos de grau zero evita que a análise ativa confunda cadastro aeroportuário com conectividade aérea.
- O SoundGraph usa reduções, filtros e limites de renderização para equilibrar volume de dados e desempenho no navegador.
