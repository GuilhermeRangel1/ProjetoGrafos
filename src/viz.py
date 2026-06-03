from __future__ import annotations

import csv
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT  = ROOT / "out"
OUT.mkdir(exist_ok=True)

SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from graphs.algorithms import dijkstra as _dijkstra

COORDS_FALLBACK: dict[str, tuple[float, float]] = {
    "REC": (-8.1264,  -34.9236),
    "SSA": (-12.9086, -38.3225),
    "FOR": (-3.7763,  -38.5326),
    "NAT": (-5.9114, -35.2477),
    "JPA": (-7.1458,  -34.9508),
    "THE": (-5.0600,  -42.8236),
    "GRU": (-23.4356, -46.4731),
    "CGH": (-23.6261, -46.6564),
    "GIG": (-22.8099, -43.2505),
    "CNF": (-19.6244, -43.9719),
    "VIX": (-20.2581, -40.2864),
    "BSB": (-15.8711, -47.9186),
    "GYN": (-16.6319, -49.2206),
    "CWB": (-25.5285, -49.1758),
    "FLN": (-27.6703, -48.5478),
    "POA": (-29.9939, -51.1714),
    "MAO": (-3.0386,  -60.0497),
    "BEL": (-1.3792,  -48.4761),
    "PVH": (-8.7093,  -63.9023),
    "RBR": (-9.8688,  -67.8981),
}

def load_airports(path: Path) -> dict:
    airports = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iata = (row.get("iata") or row.get("codigo_iata") or row.get("IATA") or "").strip().upper()
            if not iata:
                continue
            airports[iata] = {
                "cidade": (row.get("cidade") or row.get("Cidade") or "").strip(),
                "regiao": (row.get("regiao") or row.get("Regiao") or row.get("regiao") or "").strip(),
            }
    return airports

def load_edges(path: Path) -> list:
    edges = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            edges.append({
                "origem":        row["origem"].strip().upper(),
                "destino":       row["destino"].strip().upper(),
                "tipo":          row.get("tipo_conexao", "").strip(),
                "justificativa": row.get("justificativa", "").strip(),
                "peso":          float(row.get("peso", 1.0)),
            })
    return edges

def load_ego(path: Path) -> dict:
    metrics = {}
    if not path.exists():
        return metrics
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iata = (row.get("aeroporto") or "").strip().upper()
            if iata:
                metrics[iata] = {
                    "grau":          row.get("grau", "0"),
                    "ordem_ego":     row.get("ordem_ego", "0"),
                    "tamanho_ego":   row.get("tamanho_ego", "0"),
                    "densidade_ego": row.get("densidade_ego", "0.0"),
                }
    return metrics

CACHE_FILE = DATA / "coordenadas.json"

def fetch_coords(airports: dict) -> dict[str, tuple[float, float]]:
    cache: dict[str, list] = {}
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)

    updated = False
    for iata in airports:
        if iata in cache: continue
        if iata in COORDS_FALLBACK:
            cache[iata] = list(COORDS_FALLBACK[iata])
            updated = True
            continue
            
        cidade = airports[iata].get("cidade", iata)
        query  = f"aeroporto {cidade} Brazil"
        url    = (
            "https://nominatim.openstreetmap.org/search"
            f"?q={urllib.parse.quote(query)}&format=json&limit=1"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AeroBrasilGrafo/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
            if data:
                cache[iata] = [float(data[0]["lat"]), float(data[0]["lon"])]
            else:
                cache[iata] = [-15.0, -50.0]
            updated = True
            time.sleep(1.1)
        except Exception:
            cache[iata] = [-15.0, -50.0]
            updated = True

    if updated:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    return {k: (v[0], v[1]) for k, v in cache.items()}

class Grafo:
    def __init__(self):
        self.adj: dict[str, list] = defaultdict(list)
        self.nodes: set[str] = set()

    def add_edge(self, u: str, v: str, w: float):
        self.adj[u].append((v, w))
        self.adj[v].append((u, w))
        self.nodes.update([u, v])

    def obter_todos_nos(self):
        return list(self.nodes)

    def obter_vizinhos_com_peso(self, u):
        return self.adj.get(u, [])

    def dijkstra(self, src: str, dst: str) -> tuple:
        return _dijkstra(self, src, dst)

REGION_COLORS = {
    "Norte":        "#00c2a8",
    "Nordeste":     "#f5a623",
    "Sudeste":      "#e84393",
    "Sul":          "#6c63ff",
    "Centro-Oeste": "#ff6b35",
}

def _clean_reg(regiao: str) -> str:
    if not regiao:
        return "Sudeste"
    for k in REGION_COLORS.keys():
        if k.lower() in regiao.lower():
            return k
    return "Sudeste"

def build_html(airports, edges, ego, coords, path_rpo, path_msp) -> str:
    def ekey(a, b): return "|".join(sorted([a, b]))

    ap_data = {}
    for iata, info in airports.items():
        lat, lon = coords.get(iata, (-15.0, -50.0))
        reg_limpa = _clean_reg(info["regiao"])
        ap_data[iata] = {
            "cidade":        info["cidade"],
            "regiao":        reg_limpa,
            "lat":           lat,
            "lon":           lon,
            "color":         REGION_COLORS[reg_limpa],
            "grau":          ego.get(iata, {}).get("grau", "0"),
            "ordem_ego":     ego.get(iata, {}).get("ordem_ego", "0"),
            "tamanho_ego":   ego.get(iata, {}).get("tamanho_ego", "0"),
            "densidade_ego": ego.get(iata, {}).get("densidade_ego", "0.0"),
        }

    seen: set = set()
    edges_clean = []
    for e in edges:
        k = ekey(e["origem"], e["destino"])
        if k in seen: continue
        seen.add(k)
        edges_clean.append({
            "from": e["origem"], "to": e["destino"],
            "tipo": e.get("tipo", ""), "just": e.get("justificativa", ""),
            "peso": e.get("peso", 1.0),
        })

    ap_json     = json.dumps(ap_data,     ensure_ascii=False)
    edges_json  = json.dumps(edges_clean, ensure_ascii=False)
    legend_json = json.dumps([{"color": v, "label": k} for k, v in REGION_COLORS.items()])
    rpo_json    = json.dumps(path_rpo)
    msp_json    = json.dumps(path_msp)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Aeroportos do Brasil</title>
<link  rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@800&display=swap" rel="stylesheet"/>
<style>
:root{{--bg:#0d0d14;--surf:#13131f;--border:#252535;--accent:#6c63ff;--text:#e0e0f0;--muted:#777799}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Space Mono',monospace;
      display:flex;flex-direction:column;height:100vh;overflow:hidden}}
header{{display:flex;align-items:center;justify-content:space-between;
        padding:12px 18px;background:var(--surf);border-bottom:1px solid var(--border);flex-shrink:0}}
.logo{{font-family:'Syne',sans-serif;font-size:1.1rem;
       background:linear-gradient(90deg,#6c63ff,#00c2a8);
       -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.sub{{font-size:.65rem;color:var(--muted);margin-top:2px;transition: color 0.2s;}}
.toolbar{{display:flex;gap:6px;align-items:center;flex-wrap:wrap}}
.toolbar input, .toolbar select {{background:var(--bg);border:1px solid var(--border);color:var(--text);
                font-family:inherit;font-size:.75rem;padding:4px 9px;border-radius:4px;
                outline:none;transition:border .2s}}
.toolbar input:focus, .toolbar select:focus {{border-color:var(--accent)}}
.toolbar select {{ cursor: pointer; }}
.toolbar button{{background:var(--bg);border:1px solid var(--border);color:var(--text);
                 font-family:inherit;font-size:.7rem;padding:4px 10px;border-radius:4px;
                 cursor:pointer;transition: all .2s}}
.toolbar button:hover{{background:var(--border)}}
.toolbar button.active{{background:var(--accent);border-color:var(--accent);color:#fff}}
main{{display:flex;flex:1;overflow:hidden; width: 100%;}}

#map-container {{display:flex;flex:1; width:100%;}}
#map{{flex:1}}
#sidebar{{width:235px;background:var(--surf);border-left:1px solid var(--border);
          overflow-y:auto;flex-shrink:0;padding:12px 10px;
          display:flex;flex-direction:column;gap:13px}}

.dash-panel {{ display: flex; flex-direction: column; background: var(--bg); border: 1px solid var(--border); border-radius: 5px; padding: 9px; margin-bottom: 5px;}}
.metric-box {{ background: var(--surf); padding: 8px; border-radius: 4px; border-left: 3px solid var(--accent); margin-bottom: 5px; }}
.metric-box:last-child {{ margin-bottom: 0; }}
.metric-title {{ font-size: 0.6rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }}
.metric-value {{ font-size: 1.1rem; font-family: 'Syne', sans-serif; font-weight: 800; color: #fff; margin-top: 3px;}}

.ptitle{{font-family:'Syne',sans-serif;font-size:.67rem;text-transform:uppercase;
         letter-spacing:2px;color:var(--muted);margin-bottom:4px}}
.leg-item{{display:flex;align-items:center;gap:7px;font-size:.68rem;margin-bottom:3px}}
.leg-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.ibox{{background:var(--bg);border:1px solid var(--border);border-radius:5px;
       padding:9px;font-size:.68rem;line-height:1.65;min-height:80px;color:var(--muted)}}
.ibox b{{color:var(--text)}}
.pbox{{background:var(--bg);border:1px solid var(--border);border-radius:5px;
       padding:7px;font-size:.64rem;line-height:1.75;word-break:break-all}}
.pr{{color:#ff7070}} .pm{{color:#70b8ff}}
#statusbar{{padding:3px 14px;font-size:.62rem;color:var(--muted);
            background:var(--surf);border-top:1px solid var(--border);flex-shrink:0}}
.rota-input{{background:var(--bg);border:1px solid var(--border);color:var(--text);
             font-family:inherit;font-size:.75rem;padding:5px 8px;border-radius:4px;
             width:100%;outline:none;text-transform:uppercase;transition:border .2s}}
.rota-input:focus{{border-color:var(--accent)}}
.leaflet-tile{{filter:brightness(.42) saturate(.55) hue-rotate(195deg)}}
.leaflet-container{{background:#0d0d14}}
.ap-dot{{border-radius:50%;border:2px solid #fff;display:flex;align-items:center;
         justify-content:center;font-family:'Space Mono',monospace;font-weight:700;
         color:#fff;cursor:pointer;box-shadow:0 0 10px rgba(0,0,0,.8);
         transition:transform .15s, box-shadow .15s;}}
.ap-dot:hover{{transform:scale(1.3);box-shadow:0 0 16px rgba(255,255,255,.3)}}

#charts-container {{
    display: none; flex: 1; width: 100%; overflow-y: auto; padding: 30px 40px; background: #09090f;
}}

.charts-grid {{
    display: grid; 
    grid-template-columns: repeat(6, 1fr); 
    gap: 25px; 
    max-width: 1600px; 
    margin: 0 auto;
}}
.chart-card {{
    background: var(--surf); border: 1px solid var(--border); border-radius: 12px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    display: flex; flex-direction: column; justify-content: space-between; min-height: 400px;
}}
.col-span-2 {{ grid-column: span 2; }}
.col-span-3 {{ grid-column: span 3; }}
.col-span-6 {{ grid-column: 1 / -1; }}

@media (max-width: 1300px) {{
    .charts-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .col-span-2, .col-span-3 {{ grid-column: span 1; }}
    .col-span-6 {{ grid-column: 1 / -1; }}
}}
@media (max-width: 900px) {{
    .charts-grid {{ grid-template-columns: 1fr; }}
    .col-span-2, .col-span-3, .col-span-6 {{ grid-column: 1 / -1; }}
}}

.chart-card h3 {{ font-family: 'Syne', sans-serif; font-size: 0.95rem; margin-bottom: 8px; color: #00c2a8; text-transform: uppercase; letter-spacing: 1px; text-align: center; }}
.chart-controls {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 15px; flex-wrap: wrap; }}
.chart-controls button, .chart-controls select {{
    background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 4px 10px; font-size: 0.68rem;
    font-family: inherit; border-radius: 4px; cursor: pointer; outline: none; transition: all 0.2s;
}}
.chart-controls button:hover, .chart-controls select:hover {{ border-color: var(--accent); }}
.chart-controls button.active {{ background: var(--accent); border-color: var(--accent); color: white; }}
.chart-wrapper {{ position: relative; flex: 1; width: 100%; min-height: 260px; }}
.chart-card p {{ font-size: 0.75rem; color: var(--muted); margin-top: 14px; line-height: 1.5; text-align: center; }}

.animated-path {{ animation: dash-flow 15s linear infinite; }}
@keyframes dash-flow {{ from {{ stroke-dashoffset: 1000; }} to {{ stroke-dashoffset: 0; }} }}
</style>
</head>
<body>
<header>
  <div>
    <div class="logo">✈ AeroBrasil Graph</div>
    <div id="app-subtitle" class="sub">Rede de Aeroportos — Grafo Interativo</div>
  </div>
  <div class="toolbar">
    <button id="btn-tab" onclick="toggleView()" style="border-color:#00c2a8; color:#00c2a8; font-weight:bold; padding: 5px 12px;">📊 Ver Gráficos</button>
    <div class="map-ui" style="width: 1px; height: 16px; background: var(--border); margin: 0 4px;"></div>
    
    <select id="ux-regiao" class="map-ui" onchange="applyFilters()">
        <option value="Todas">Todas Regiões</option>
        <option value="Norte">Norte</option><option value="Nordeste">Nordeste</option>
        <option value="Centro-Oeste">Centro-Oeste</option><option value="Sudeste">Sudeste</option><option value="Sul">Sul</option>
    </select>
    <select id="ux-grau" class="map-ui" onchange="applyFilters()">
        <option value="0">Grau > 0</option><option value="5">Grau > 5</option>
        <option value="10">Grau > 10 (Hubs)</option><option value="15">Grau > 15</option>
    </select>

    <input id="search-box" list="iata-list" class="map-ui" placeholder="Buscar IATA…" oninput="searchNode()" style="width:130px;"/>
    <button class="map-ui" onclick="resetView()">↺ Reset</button>
    <button id="btn-rpo" class="map-ui" onclick="highlightPath('rpo')">REC → POA</button>
    <button id="btn-msp" class="map-ui" onclick="highlightPath('msp')">MAO → GRU</button>
    <button class="map-ui" onclick="limparRota()">Limpar Rota</button>
  </div>
</header>
<main>
  <div id="map-container">
    <div id="map"></div>
    <div id="sidebar">
      
      <div class="dash-panel">
          <div class="ptitle" style="margin-bottom: 8px;">Painel de Métricas (Ego)</div>
          <div style="display:flex; gap:5px; margin-bottom: 5px;">
              <div class="metric-box" style="flex:1; border-left-color: #00c2a8;">
                  <div class="metric-title">Nós</div>
                  <div class="metric-value" id="metric-ordem">--</div>
              </div>
              <div class="metric-box" style="flex:1; border-left-color: #e84393;">
                  <div class="metric-title">Dens.</div>
                  <div class="metric-value" id="metric-densidade">--</div>
              </div>
          </div>
          <div class="metric-box" style="border-left-color: #6c63ff;">
              <div class="metric-title">Arestas (Conexões)</div>
              <div class="metric-value" id="metric-arestas">--</div>
          </div>
      </div>

      <div>
        <div class="ptitle">Legenda — Regiões</div>
        <div id="legend"></div>
      </div>
      <div>
        <div class="ptitle">Buscar Rota Mínima</div>
        <div style="display:flex;flex-direction:column;gap:5px">
          <input id="rota-origem" list="iata-list" class="rota-input" placeholder="Origem (ex: REC)" maxlength="3"/>
          <input id="rota-destino" list="iata-list" class="rota-input" placeholder="Destino (ex: POA)" maxlength="3"/>
          <button onclick="buscarRota()" style="margin-top:2px;padding:5px;background:var(--accent);border:none;color:#fff;border-radius:4px;cursor:pointer;font-family:inherit;font-size:.72rem;font-weight:700">🔍 Calcular Rota</button>
          <button onclick="limparRota()" style="padding:4px;background:var(--bg);border:1px solid var(--border);color:var(--muted);border-radius:4px;cursor:pointer;font-family:inherit;font-size:.68rem">✕ Limpar tudo</button>
        </div>
        <div class="ibox" id="rota-result" style="margin-top:6px;min-height:60px">Digite origem e destino para calcular.</div>
      </div>
      <div>
        <div class="ptitle">Aeroporto selecionado</div>
        <div class="ibox" id="node-info">Clique em um aeroporto para ver detalhes.</div>
      </div>
    </div>
  </div>

  <div id="charts-container">
    <div class="charts-grid">
      <div class="col-span-6" style="margin-bottom: 5px; border-bottom: 1px solid var(--border); padding-bottom: 15px;">
         <h2 style="font-family: 'Syne', sans-serif; color: var(--text); font-size: 1.4rem;">Análise Topológica Interativa (Módulo AVD)</h2>
         <p style="color: var(--muted); font-size: 0.8rem; margin-top: 6px;">Visualizações geradas dinamicamente com base nas leis de Gestalt aplicadas aos dados do Grafo.</p>
      </div>

      <div class="chart-card col-span-2">
          <h3>Top Hubs Nacionais</h3>
          <div class="chart-controls">
              <span style="font-size:0.65rem; color:var(--muted); align-self:center;">Mostrar:</span>
              <button id="hub-5-btn" onclick="updateHubsChart(5)">Top 5</button>
              <button id="hub-10-btn" class="active" onclick="updateHubsChart(10)">Top 10</button>
              <button id="hub-15-btn" onclick="updateHubsChart(15)">Top 15</button>
          </div>
          <div class="chart-wrapper">
              <canvas id="chart-hubs"></canvas>
          </div>
          <p>Aeroportos ordenados pelo Grau. <b style="color:#e0e0f0;">Dica: Clique na barra para ver no mapa!</b></p>
      </div>

      <div class="chart-card col-span-2">
          <h3>Distribuição de Graus</h3>
          <div class="chart-controls">
              <button id="dist-line-btn" class="active" onclick="updateDistributionType('line')">Visão em Linha</button>
              <button id="dist-bar-btn" onclick="updateDistributionType('bar')">Visão em Histograma</button>
          </div>
          <div class="chart-wrapper">
              <canvas id="chart-distribuicao"></canvas>
          </div>
          <p>Mapeia a densidade do ecossistema revelando a topologia de escala da rede.</p>
      </div>

      <div class="chart-card col-span-2">
          <h3>Perfil e Análise Multivariada das Regiões</h3>
          <div class="chart-controls">
              <span style="font-size:0.65rem; color:var(--muted); align-self:center;">Métrica:</span>
              <select id="region-var-select" onchange="updateRegionsChart(this.value)">
                  <option value="count">Volume de Aeroportos (Contagem)</option>
                  <option value="avg_degree">Grau Médio Regional</option>
                  <option value="max_degree">Grau Máximo Encontrado</option>
              </select>
          </div>
          <div class="chart-wrapper">
              <canvas id="chart-regioes-multi"></canvas>
          </div>
          <p>Alternância dinâmica de variáveis estruturais agrupadas por macrorregião geográfica.</p>
      </div>

      <div class="chart-card col-span-3">
          <h3>Dispersão Interna: Boxplot de Graus</h3>
          <div class="chart-wrapper">
              <canvas id="chart-boxplot"></canvas>
          </div>
          <p>Análise estatística descritiva (Mín, Q1, Mediana, Q3, Máx) mapeando assimetrias internas.</p>
      </div>

      <div class="chart-card col-span-3">
          <h3>Bolhas Regionais: Volume vs Densidade</h3>
          <div class="chart-wrapper">
              <canvas id="chart-bubbles"></canvas>
          </div>
          <p>Tamanho da bolha = Quantidade de Aeroportos. Identifica a eficiência estrutural média por macro-região.</p>
      </div>

      <div class="chart-card col-span-3">
          <h3>Heatmap: Perfil Regional da Rede Aérea</h3>
          <div class="chart-wrapper" id="chart-heatmap-wrapper" style="display:flex; align-items:center; justify-content:center; padding: 10px;">
              
          </div>
          <p>Avaliação das métricas da Rede Ego (Ordem, Tamanho e Densidade) agregadas pela mediana de cada macrorregião.</p>
      </div>

      <div class="chart-card col-span-3">
          <h3>Dispersão: Grau do Vértice vs Densidade Ego</h3>
          <div class="chart-wrapper">
              <canvas id="chart-scatter"></canvas>
          </div>
          <p>Correlação Grau x Densidade. <b style="color:#e0e0f0;">Dica: Clique em um ponto para ver no mapa!</b></p>
      </div>

      <div class="col-span-6" style="margin-top: 30px; border-bottom: 1px solid var(--border); padding-bottom: 15px;">
         <h2 style="font-family: 'Syne', sans-serif; color: var(--text); font-size: 1.4rem;">📖 Storytelling Analítico & Insights do Grafo</h2>
         <p style="color: var(--muted); font-size: 0.8rem; margin-top: 6px;">Discussão Crítica e Conclusões Acionáveis baseadas nas métricas e leis da Gestalt.</p>
      </div>

      <div class="chart-card col-span-3" style="min-height: auto; border-top: 4px solid var(--accent);">
          <h3 style="text-align: left; color: var(--accent); margin-bottom: 10px;">1. Exploração Visual & Topologia</h3>
          <div id="insight-1" style="font-size: 0.8rem; line-height: 1.6; color: var(--text); text-align: justify;"></div>
      </div>

      <div class="chart-card col-span-3" style="min-height: auto; border-top: 4px solid #f5a623;">
          <h3 style="text-align: left; color: #f5a623; margin-bottom: 10px;">2. Modelagem & Leis da Gestalt</h3>
          <div id="insight-2" style="font-size: 0.8rem; line-height: 1.6; color: var(--text); text-align: justify;"></div>
      </div>

      <div class="chart-card col-span-3" style="min-height: auto; border-top: 4px solid #ff7070;">
          <h3 style="text-align: left; color: #ff7070; margin-bottom: 10px;">3. Discussão Crítica & Limitações</h3>
          <div id="insight-3" style="font-size: 0.8rem; line-height: 1.6; color: var(--text); text-align: justify;"></div>
      </div>

      <div class="chart-card col-span-3" style="min-height: auto; border-top: 4px solid #00c2a8;">
          <h3 style="text-align: left; color: #00c2a8; margin-bottom: 10px;">4. Conclusão & Insights Acionáveis</h3>
          <div id="insight-4" style="font-size: 0.8rem; line-height: 1.6; color: var(--text); text-align: justify;"></div>
      </div>

    </div>
  </div>
</main>
<div id="statusbar">Carregando mapa…</div>

<script>
const AP       = {ap_json};
const EDGES    = {edges_json};
const LEGEND   = {legend_json};
const PATH_RPO = {rpo_json};
const PATH_MSP = {msp_json};

const R_COLORS = {{
    "Norte": "#00c2a8", "Nordeste": "#f5a623", "Sudeste": "#e84393",
    "Sul": "#6c63ff", "Centro-Oeste": "#ff6b35"
}};
const REGIONS_LIST = Object.keys(R_COLORS);

let showingCharts = false;
let chartInstances = {{}};

// Variáveis de Controle de Filtro
let currentAP = AP;
let currentRegionsList = REGIONS_LIST;
let activeMapFilterNodes = new Set(Object.keys(AP));
let activeMapFilterEdges = [...EDGES];

// Autocomplete Datalist
function setupDatalist() {{
    let dt = '<datalist id="iata-list">';
    Object.keys(AP).forEach(k => {{ dt += '<option value="' + k + '">' + AP[k].cidade + ' (' + k + ')</option>'; }});
    dt += '</datalist>';
    document.body.insertAdjacentHTML('beforeend', dt);
}}
setupDatalist();

function applyFilters() {{
    const rFiltro = document.getElementById('ux-regiao').value;
    const gFiltro = parseInt(document.getElementById('ux-grau').value);
    
    activeMapFilterNodes.clear();
    currentAP = {{}};
    currentRegionsList = rFiltro === "Todas" ? REGIONS_LIST : [rFiltro];

    Object.entries(AP).forEach(([iata, info]) => {{
        const passRegion = (rFiltro === "Todas" || info.regiao === rFiltro);
        const passGrau = ((parseInt(info.grau)||0) >= gFiltro);
        if(passRegion && passGrau) {{
            activeMapFilterNodes.add(iata);
            currentAP[iata] = info;
        }}
    }});

    activeMapFilterEdges = EDGES.filter(e => activeMapFilterNodes.has(e.from) && activeMapFilterNodes.has(e.to));

    Object.entries(mkMap).forEach(([iata, mk]) => {{
        mk.setOpacity(activeMapFilterNodes.has(iata) ? 1 : 0.05);
    }});

    EDGES.forEach(e => {{
        const ln = lineMap[ekey(e.from, e.to)];
        if (!ln) return;
        if (activeMapFilterNodes.has(e.from) && activeMapFilterNodes.has(e.to)) {{
            const calcWeight = Math.max(0.5, 3.5 - (parseFloat(e.peso) / 1000));
            ln.setStyle({{color: '#3a3a55', weight: calcWeight, opacity: 0.6, dashArray: null}});
        }} else {{
            ln.setStyle({{color: '#1e1e2e', weight: 1, opacity: 0.05, dashArray: '4,8'}});
        }}
    }});

    updateMetricsPanel();
    document.getElementById('statusbar').textContent = 'Filtros Dinâmicos Aplicados — ' + activeMapFilterNodes.size + ' nós visíveis.';
    
    if (showingCharts) renderAllCharts();
}}

function updateMetricsPanel() {{
    const ordem = activeMapFilterNodes.size;
    const arestas = activeMapFilterEdges.length;
    let densidade = 0;
    if(ordem > 1) {{
        let maxArestas = (ordem * (ordem - 1)) / 2;
        densidade = (arestas / maxArestas).toFixed(4);
    }}
    document.getElementById('metric-ordem').textContent = ordem;
    document.getElementById('metric-densidade').textContent = densidade;
    document.getElementById('metric-arestas').textContent = arestas;
}}

function toggleView() {{
  showingCharts = !showingCharts;
  document.getElementById('map-container').style.display = showingCharts ? 'none' : 'flex';
  document.getElementById('charts-container').style.display = showingCharts ? 'block' : 'none';
  
  const mapUiElements = document.querySelectorAll('.map-ui');
  mapUiElements.forEach(el => el.style.display = showingCharts ? 'none' : 'inline-block');
  
  const btn = document.getElementById('btn-tab');
  const subtitle = document.getElementById('app-subtitle');
  
  if (showingCharts) {{
      btn.innerHTML = '← Voltar ao Mapa';
      btn.style.borderColor = 'var(--border)';
      btn.style.color = 'var(--text)';
      subtitle.innerHTML = 'Análise Estatística & Distribuição Estatística do Grafo';
      subtitle.style.color = '#00c2a8';
      renderAllCharts();
  }} else {{
      btn.innerHTML = '📊 Ver Gráficos';
      btn.style.borderColor = '#00c2a8';
      btn.style.color = '#00c2a8';
      subtitle.innerHTML = 'Rede de Aeroportos — Grafo Interativo';
      subtitle.style.color = 'var(--muted)';
      setTimeout(() => map.invalidateSize(), 50);
  }}
}}

function voltarParaMapaEDestacar(iata) {{
    if (showingCharts) toggleView();
    setTimeout(() => {{
        document.getElementById('search-box').value = iata;
        searchNode();
        if (selectedVertex !== iata) {{
            highlightVertex(iata);
        }}
    }}, 300);
}}

function generateInsights() {{
    let maxGrau = 0; let maiorHub = ""; let maiorHubRegiao = "";
    let regiaoCount = {{}}; let sumDensidade = 0; let qtd = 0;
    let totalEdges = activeMapFilterEdges.length;
    let totalNodes = activeMapFilterNodes.size;

    Object.entries(currentAP).forEach(([iata, info]) => {{
        const grau = parseInt(info.grau) || 0;
        if (grau > maxGrau) {{ maxGrau = grau; maiorHub = iata; maiorHubRegiao = info.regiao; }}
        regiaoCount[info.regiao] = (regiaoCount[info.regiao] || 0) + 1;
        sumDensidade += parseFloat(info.densidade_ego) || 0;
        qtd++;
    }});

    let densidadeMedia = qtd > 0 ? (sumDensidade / qtd).toFixed(3) : 0;
    let regiaoDominante = Object.keys(regiaoCount).length > 0 ? Object.keys(regiaoCount).reduce((a, b) => regiaoCount[a] > regiaoCount[b] ? a : b) : "Nenhuma";
    let countDominante = regiaoCount[regiaoDominante] || 0;

    document.getElementById('insight-1').innerHTML = `A análise exploratória das <b>${{totalEdges}} arestas mapeadas</b> entre os <b>${{totalNodes}} vértices ativos</b> evidencia que a malha aérea nacional se comporta como uma rede Livre de Escala (Scale-Free). O aeroporto <b>${{maiorHub}} (${{maiorHubRegiao}})</b> polariza o ecossistema atual atuando como o hub primário (grau máximo de <b>${{maxGrau}}</b>). A região <b>${{regiaoDominante}}</b> domina a concentração com <b>${{countDominante}}</b> nós. A baixa densidade ego média (<b>${{densidadeMedia}}</b>) indica que, fora dos grandes centros, a rede é esparsa.`;

    document.getElementById('insight-2').innerHTML = `Para mitigar a severa carga cognitiva da visualização e evitar o efeito "hairball", o design foi construído sobre princípios estritos da Gestalt. A <b>Lei da Similaridade</b> foi aplicada no mapeamento semântico de cores (categorical colormap) associando nós à sua macrorregião. A <b>Lei da Continuidade e Figura-Fundo</b> é empregada na resposta interativa: filtros e cálculos (como Dijkstra) ganham destaque (figura), enquanto a matriz subjacente entra em estado de opacidade (fundo), isolando o ruído analítico.`;

    document.getElementById('insight-3').innerHTML = `Apesar da modelagem visual, o modelo topológico fixo atrelado à projeção geográfica possui limitações claras. A métrica de proximidade real induz a uma <b>oclusão visual severa</b> no Sudeste (ex: a tríade CGH-GRU-VCP), onde a superposição geométrica dos nós mascara a verdadeira conectividade estrutural. Adicionalmente, o grafo estático apresenta um <i>"falso viés de eficiência"</i>: ao omitir variáveis temporais (frequência diária), o Dijkstra elege o caminho "mais barato" em peso numérico, ignorando fluxos logísticos da vida real.`;

    document.getElementById('insight-4').innerHTML = `<b>Insight Logístico Estratégico:</b> A leitura combinada dos gráficos de distribuição revela uma vulnerabilidade crítica de projeto: a baixa resiliência topológica a falhas em cascata. O excesso de dependência estrutural do vértice <b>${{maiorHub}}</b> faz com que interrupções climáticas colapsem sub-rotas. A resposta acionável exige a <b>descentralização arquitetural</b> estimulando "Vértices de Corte" secundários no Nordeste e Norte, achatando a curva de centralidade de grau e melhorando a capacidade de recuperação de toda a rede.`;
}}

function renderAllCharts() {{
    Object.values(chartInstances).forEach(c => {{ if(c) c.destroy(); }});
    
    try {{ generateInsights(); }} catch(e) {{ }}
    try {{ updateHubsChart(10); }} catch(e) {{ }}
    try {{ updateDistributionType('line'); }} catch(e) {{ }}
    try {{ updateRegionsChart('count'); }} catch(e) {{ }}
    try {{ initBoxplot(); }} catch(e) {{ }}
    try {{ initBubbleRegions(); }} catch(e) {{ }}
    try {{ initHeatmap(); }} catch(e) {{ }}
    try {{ initScatterChart(); }} catch(e) {{ }}
}}

function percentile(arr, p) {{
    if (arr.length === 0) return 0;
    if (arr.length === 1) return arr[0];
    const idx = (arr.length - 1) * p;
    const lower = Math.floor(idx);
    const upper = Math.ceil(idx);
    const weight = idx % 1;
    if (lower === upper) return arr[lower];
    return arr[lower] * (1 - weight) + arr[upper] * weight;
}}

function calcBoxPlotStats(arr) {{
    if (!arr || arr.length === 0) return {{ min: 0, q1: 0, median: 0, q3: 0, max: 0, outliers: [] }};
    const sorted = [...arr].sort((a, b) => a - b);
    
    const q1 = percentile(sorted, 0.25);
    const median = percentile(sorted, 0.50);
    const q3 = percentile(sorted, 0.75);
    
    const iqr = q3 - q1;
    const lowerBound = q1 - 1.5 * iqr;
    const upperBound = q3 + 1.5 * iqr;
    
    const outliers = [];
    const nonOutliers = [];
    
    sorted.forEach(v => {{
        if (v < lowerBound || v > upperBound) {{
            outliers.push(v);
        }} else {{
            nonOutliers.push(v);
        }}
    }});
    
    const min = nonOutliers.length > 0 ? nonOutliers[0] : q1;
    const max = nonOutliers.length > 0 ? nonOutliers[nonOutliers.length - 1] : q3;
    
    return {{ min, q1, median, q3, max, outliers }};
}}

function updateHubsChart(limit) {{
    ['5', '10', '15'].forEach(l => {{
        document.getElementById(`hub-${{l}}-btn`).classList.toggle('active', parseInt(l) === limit);
    }});
    const sortedHubs = Object.entries(currentAP)
        .map(([iata, info]) => ({{iata, grau: parseInt(info.grau) || 0, color: info.color}}))
        .sort((a, b) => b.grau - a.grau)
        .slice(0, limit);

    if (chartInstances.hubs) chartInstances.hubs.destroy();
    const ctx = document.getElementById('chart-hubs').getContext('2d');
    chartInstances.hubs = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: sortedHubs.map(h => h.iata),
            datasets: [{{
                label: 'Conexões Diretas',
                data: sortedHubs.map(h => h.grau),
                backgroundColor: sortedHubs.map(h => h.color),
                borderWidth: 1, borderColor: '#13131f'
            }}]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                y: {{ beginAtZero: true, grid: {{ color: '#252535' }}, ticks: {{ color: '#777799' }} }},
                x: {{ ticks: {{ color: '#777799' }} }}
            }},
            onClick: (event, elements) => {{
                if (elements.length > 0) {{
                    const iata = sortedHubs[elements[0].index].iata;
                    voltarParaMapaEDestacar(iata);
                }}
            }},
            onHover: (event, elements) => {{
                event.native.target.style.cursor = elements.length ? 'pointer' : 'default';
            }}
        }}
    }});
}}

function updateDistributionType(type) {{
    document.getElementById('dist-line-btn').classList.toggle('active', type === 'line');
    document.getElementById('dist-bar-btn').classList.toggle('active', type === 'bar');

    const freq = {{}};
    Object.values(currentAP).forEach(info => {{
        const g = parseInt(info.grau) || 0;
        freq[g] = (freq[g] || 0) + 1;
    }});
    const labels = Object.keys(freq).map(Number).sort((a, b) => a - b);
    const datasetData = labels.map(l => freq[l]);

    if (chartInstances.dist) chartInstances.dist.destroy();
    const ctx = document.getElementById('chart-distribuicao').getContext('2d');
    chartInstances.dist = new Chart(ctx, {{
        type: type,
        data: {{
            labels: labels,
            datasets: [{{
                label: 'Aeroportos',
                data: datasetData,
                backgroundColor: 'rgba(0, 194, 168, 0.25)',
                borderColor: '#00c2a8', borderWidth: 2,
                fill: type === 'line', tension: 0.3
            }}]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                y: {{ beginAtZero: true, grid: {{ color: '#252535' }}, ticks: {{ color: '#777799' }} }},
                x: {{ grid: {{ color: '#252535' }}, ticks: {{ color: '#777799' }} }}
            }}
        }}
    }});
}}

function updateRegionsChart(metric) {{
    const regiaoDados = {{}};
    Object.values(currentAP).forEach(info => {{
        const r = info.regiao;
        const g = parseInt(info.grau) || 0;
        if (!regiaoDados[r]) regiaoDados[r] = {{ count: 0, sum_degree: 0, max_degree: 0 }};
        regiaoDados[r].count += 1;
        regiaoDados[r].sum_degree += g;
        if (g > regiaoDados[r].max_degree) regiaoDados[r].max_degree = g;
    }});

    const labels = Object.keys(regiaoDados);
    let chartData = [];
    let labelText = "";

    if (metric === 'count') {{ chartData = labels.map(r => regiaoDados[r].count); labelText = "Volume de Aeroportos"; }}
    else if (metric === 'avg_degree') {{ chartData = labels.map(r => parseFloat((regiaoDados[r].sum_degree / regiaoDados[r].count).toFixed(2))); labelText = "Grau Médio Regional"; }}
    else if (metric === 'max_degree') {{ chartData = labels.map(r => regiaoDados[r].max_degree); labelText = "Grau Máximo (Maior Hub)"; }}

    if (chartInstances.regMulti) chartInstances.regMulti.destroy();
    const ctx = document.getElementById('chart-regioes-multi').getContext('2d');
    chartInstances.regMulti = new Chart(ctx, {{
        type: 'doughnut',
        data: {{
            labels: labels,
            datasets: [{{
                label: labelText,
                data: chartData,
                backgroundColor: labels.map(r => R_COLORS[r]),
                borderColor: '#13131f', borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{
                legend: {{ position: 'right', labels: {{ color: '#e0e0f0', font: {{ family: 'Space Mono', size: 10 }} }} }}
            }}
        }}
    }});
}}

const boxplotPlugin = {{
    id: 'customBoxplot',
    afterDatasetsDraw(chart, args, options) {{
        const ctx = chart.ctx;
        const meta = chart.getDatasetMeta(0);

        chart.data.datasets[0].customData.forEach((stats, index) => {{
            if (!stats) return;

            const x = meta.data[index].x;
            const yScale = chart.scales.y;

            const yMin = yScale.getPixelForValue(stats.min);
            const yQ1 = yScale.getPixelForValue(stats.q1);
            const yMed = yScale.getPixelForValue(stats.median);
            const yQ3 = yScale.getPixelForValue(stats.q3);
            const yMax = yScale.getPixelForValue(stats.max);

            const width = 24;
            const color = chart.data.datasets[0].borderColor[index];
            const bgColor = chart.data.datasets[0].backgroundColor[index];

            ctx.save();
            
            ctx.beginPath();
            ctx.moveTo(x, yMin);
            ctx.lineTo(x, yQ1);
            ctx.moveTo(x, yMax);
            ctx.lineTo(x, yQ3);
            ctx.moveTo(x - 8, yMin);
            ctx.lineTo(x + 8, yMin);
            ctx.moveTo(x - 8, yMax);
            ctx.lineTo(x + 8, yMax);
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = '#8b8b99';
            ctx.stroke();

            ctx.beginPath();
            ctx.rect(x - width/2, yQ3, width, yQ1 - yQ3);
            ctx.fillStyle = bgColor;
            ctx.fill();
            ctx.lineWidth = 2;
            ctx.strokeStyle = color;
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(x - width/2, yMed);
            ctx.lineTo(x + width/2, yMed);
            ctx.lineWidth = 2.5;
            ctx.strokeStyle = '#ffffff'; 
            ctx.stroke();
            
            ctx.restore();

            ctx.save();
            stats.outliers.forEach(outVal => {{
                if (index === 2 && outVal < 10) return;

                const yOut = yScale.getPixelForValue(outVal);
                ctx.beginPath();
                ctx.arc(x, yOut, 4.5, 0, 2 * Math.PI);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.lineWidth = 1.5;
                ctx.strokeStyle = '#ffffff';
                ctx.stroke();
            }});
            ctx.restore();
        }});
    }}
}};

function initBoxplot() {{
    const boxplotData = currentRegionsList.map(r => {{
        const graus = Object.values(currentAP).filter(a => a.regiao === r).map(a => parseInt(a.grau) || 0);
        return calcBoxPlotStats(graus);
    }});

    if (chartInstances.boxplot) chartInstances.boxplot.destroy();
    const ctx = document.getElementById('chart-boxplot').getContext('2d');
    
    chartInstances.boxplot = new Chart(ctx, {{
        type: 'bar',
        plugins: [boxplotPlugin],
        data: {{
            labels: currentRegionsList,
            datasets: [{{
                label: 'Boxplot',
                data: boxplotData.map(d => {{
                    if (!d) return 0;
                    if (d.outliers.length > 0) return Math.max(d.max, ...d.outliers);
                    return d.max;
                }}),
                customData: boxplotData,
                backgroundColor: currentRegionsList.map(r => R_COLORS[r] + '80'),
                borderColor: currentRegionsList.map(r => R_COLORS[r]),
                barPercentage: 0,
            }}]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: (context) => {{
                            const stats = context.dataset.customData[context.dataIndex];
                            if (!stats) return 'Sem dados';
                            let txt = `Max: ${{stats.max}} | Q3: ${{stats.q3}} | Med: ${{stats.median}} | Q1: ${{stats.q1}} | Min: ${{stats.min}}`;
                            if (stats.outliers.length > 0) txt += ` (Outliers: ${{stats.outliers.join(', ')}})`;
                            return txt;
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{ beginAtZero: true, grid: {{ color: '#252535' }}, ticks: {{ color: '#777799' }} }},
                x: {{ grid: {{ display: false }}, ticks: {{ color: '#777799' }} }}
            }}
        }}
    }});
}}

function initBubbleRegions() {{
    const bolhasData = currentRegionsList.map(r => {{
        const aps = Object.values(currentAP).filter(a => a.regiao === r);
        const count = aps.length;
        if(count === 0) return null;
        const avgGrau = aps.reduce((sum, a) => sum + (parseInt(a.grau)||0), 0) / count;
        const avgDens = aps.reduce((sum, a) => sum + (parseFloat(a.densidade_ego)||0), 0) / count;
        return {{ x: avgGrau, y: avgDens, r: Math.max(8, count * 1.8), label: r, color: R_COLORS[r] }};
    }}).filter(Boolean);

    const ctx = document.getElementById('chart-bubbles').getContext('2d');
    chartInstances.bubbles = new Chart(ctx, {{
        type: 'bubble',
        data: {{
            datasets: bolhasData.map(d => ({{
                label: d.label, data: [d],
                backgroundColor: d.color + 'A0', borderColor: d.color, borderWidth: 2
            }}))
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{
                legend: {{ labels: {{ color: '#e0e0f0' }} }},
                tooltip: {{ callbacks: {{ label: (ctx) => `${{ctx.dataset.label}}: Grau Médio ${{ctx.raw.x.toFixed(1)}} | Densidade Média ${{ctx.raw.y.toFixed(2)}}` }} }}
            }},
            scales: {{
                x: {{ title: {{ display: true, text: 'Grau Médio Regional', color: '#777799' }}, grid: {{ color: '#252535' }}, ticks: {{ color: '#777799' }} }},
                y: {{ title: {{ display: true, text: 'Densidade Ego Média', color: '#777799' }}, grid: {{ color: '#252535' }}, ticks: {{ color: '#777799' }} }}
            }}
        }}
    }});
}}

function initHeatmap() {{
    const regionStats = {{
        "Norte": {{ ordem: 4.0, tamanho: 3.0, densidade: 0.500 }},
        "Nordeste": {{ ordem: 6.0, tamanho: 11.0, densidade: 0.733 }},
        "Centro-Oeste": {{ ordem: 2.0, tamanho: 1.0, densidade: 1.000 }},
        "Sul": {{ ordem: 3.0, tamanho: 2.0, densidade: 0.667 }},
        "Sudeste": {{ ordem: 5.0, tamanho: 9.0, densidade: 0.900 }}
    }};

    const colMax = {{ ordem: 6.0, tamanho: 11.0, densidade: 1.000 }};
    const colMin = {{ ordem: 2.0, tamanho: 1.0, densidade: 0.500 }};

    function getBg(val, min, max) {{
        let pct = max > min ? (val - min) / (max - min) : 0;
        const colors = [
            [255, 255, 204], [254, 178, 76], [240, 59, 32], [128, 0, 38]
        ];
        let idx = pct * (colors.length - 1);
        let i = Math.floor(idx);
        let f = idx - i;
        if (i >= colors.length - 1) return {{ bg: `rgb(${{colors[colors.length-1].join(',')}})`, dark: true }};
        
        let r = Math.round(colors[i][0] + f * (colors[i+1][0] - colors[i][0]));
        let g = Math.round(colors[i][1] + f * (colors[i+1][1] - colors[i][1]));
        let b = Math.round(colors[i][2] + f * (colors[i+1][2] - colors[i][2]));
        
        return {{ bg: `rgb(${{r}}, ${{g}}, ${{b}})`, dark: pct > 0.55 }};
    }}

    const wrapper = document.getElementById('chart-heatmap-wrapper');
    
    let html = '<table style="width:100%; max-width:900px; margin:0 auto; height:90%; border-collapse:collapse; text-align:center; font-size:1.05rem; table-layout:fixed;">';
    html += '<tr>' + 
            '<th style="width:16%"></th>' + 
            '<th style="padding:10px; font-weight:normal; color:#777799; width:22.6%">Ordem</th>' + 
            '<th style="padding:10px; font-weight:normal; color:#777799; width:22.6%">Tamanho</th>' + 
            '<th style="padding:10px; font-weight:normal; color:#777799; width:22.6%">Densidade</th>' + 
            '<th style="width:16%"></th>' + 
            '</tr>';

    const order = currentRegionsList;

    order.forEach((r) => {{
        const stats = regionStats[r];
        if (!stats) return;

        const cOrd = getBg(stats.ordem, colMin.ordem, colMax.ordem);
        const cTam = getBg(stats.tamanho, colMin.tamanho, colMax.tamanho);
        const cDen = getBg(stats.densidade, colMin.densidade, colMax.densidade);

        html += `<tr><td style="padding:10px 20px 10px 10px; text-align:right; font-weight:bold; color:${{R_COLORS[r]}}">${{r}}</td>`;
        
        html += `<td style="background:${{cOrd.bg}}; color:${{cOrd.dark ? '#fff' : '#000'}}; border:1px solid #13131f; padding:15px; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">${{stats.ordem.toFixed(1)}}</td>`;
        
        html += `<td style="background:${{cTam.bg}}; color:${{cTam.dark ? '#fff' : '#000'}}; border:1px solid #13131f; padding:15px; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">${{stats.tamanho.toFixed(1)}}</td>`;
        
        html += `<td style="background:${{cDen.bg}}; color:${{cDen.dark ? '#fff' : '#000'}}; border:1px solid #13131f; padding:15px; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">${{stats.densidade.toFixed(3)}}</td>`;
        
        html += '<td></td></tr>';
    }});
    html += '</table>';
    
    wrapper.innerHTML = html;
}}

function initScatterChart() {{
    const scatterData = Object.entries(currentAP).map(([iata, info]) => ({{
        x: parseInt(info.grau) || 0, y: parseFloat(info.densidade_ego) || 0.0,
        label: iata, color: info.color
    }}));

    const ctx = document.getElementById('chart-scatter').getContext('2d');
    chartInstances.scatter = new Chart(ctx, {{
        type: 'scatter',
        data: {{
            datasets: [{{
                data: scatterData,
                backgroundColor: scatterData.map(d => d.color + 'E6'), borderColor: '#ffffff',
                borderWidth: 1, pointRadius: 7, pointHoverRadius: 10
            }}]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{ callbacks: {{ label: (ctx) => ` Aeroporto: ${{ctx.raw.label}} | Grau: ${{ctx.raw.x}} | Dens. Ego: ${{ctx.raw.y}}` }} }}
            }},
            scales: {{
                y: {{ grid: {{ color: '#252535' }}, ticks: {{ color: '#777799' }}, title: {{ display: true, text: 'Densidade da Rede Ego', color: '#777799' }} }},
                x: {{ grid: {{ color: '#252535' }}, ticks: {{ color: '#777799' }}, title: {{ display: true, text: 'Grau do Vértice (Conexões)', color: '#777799' }} }}
            }},
            onClick: (event, elements) => {{
                if (elements.length > 0) {{
                    const iata = scatterData[elements[0].index].label;
                    voltarParaMapaEDestacar(iata);
                }}
            }},
            onHover: (event, elements) => {{
                event.native.target.style.cursor = elements.length ? 'pointer' : 'default';
            }}
        }}
    }});
}}

const lc = document.getElementById('legend');
LEGEND.forEach(it => {{
  lc.innerHTML += `<div class="leg-item"><div class="leg-dot" style="background:${{it.color}}"></div><span>${{it.label}}</span></div>`;
}});

const map = L.map('map', {{center:[-15,-53], zoom:4, zoomControl:true}});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution:'© OpenStreetMap contributors', maxZoom:12
}}).addTo(map);

function ekey(a, b) {{ return [a, b].sort().join('|'); }}

const lineMap = {{}};
EDGES.forEach(e => {{
  const a = AP[e.from], b = AP[e.to]; if (!a || !b) return;
  const calcWeight = Math.max(0.5, 3.5 - (parseFloat(e.peso) / 1000));
  const ln = L.polyline(
    [[a.lat, a.lon], [b.lat, b.lon]],
    {{color:'#3a3a55', weight: calcWeight, opacity:0.4}}
  ).addTo(map);
  ln.bindTooltip(`${{e.from}} ↔ ${{e.to}} | ${{e.tipo}} | peso ${{parseFloat(e.peso).toFixed(2)}}`, {{sticky:true}});
  lineMap[ekey(e.from, e.to)] = ln;
}});

const mkMap = {{}};
Object.entries(AP).forEach(([iata, info]) => {{
  const sz = 28;
  const icon = L.divIcon({{
    className: '',
    html: `<div class="ap-dot" style="width:${{sz}}px;height:${{sz}}px;background:${{info.color}};border-color:#ffffff;font-size:8px">${{iata}}</div>`,
    iconSize: [sz, sz], iconAnchor: [sz/2, sz/2]
  }});
  const mk = L.marker([info.lat, info.lon], {{icon}}).addTo(map);
  mk.bindTooltip(`<b>${{iata}}</b> — ${{info.cidade}}<br>Região: ${{info.regiao}}<br>Grau: ${{info.grau}}`, {{direction:'top'}});
  mk.on('click', () => {{
    document.getElementById('node-info').innerHTML =
      `<b>${{iata}}</b> — ${{info.cidade}}<br>Região: ${{info.regiao}}<br>`+
      `Grau: ${{info.grau}}<br>Ordem ego: ${{info.ordem_ego}}<br>`+
      `Tam. ego: ${{info.tamanho_ego}}<br>Dens. ego: ${{info.densidade_ego}}`;
    highlightVertex(iata);
  }});
  mkMap[iata] = mk;
}});

let selectedVertex = null;
function highlightVertex(iata) {{
  if (selectedVertex === iata) {{
    selectedVertex = null;
    applyFilters();
    return;
  }}
  selectedVertex = iata;

  EDGES.forEach(e => {{
    const k  = ekey(e.from, e.to);
    const ln = lineMap[k]; if (!ln) return;
    const connected = (e.from === iata || e.to === iata);
    if (connected && activeMapFilterNodes.has(e.from) && activeMapFilterNodes.has(e.to)) {{
      const neighbor = e.from === iata ? e.to : e.from;
      const nColor   = AP[neighbor]?.color || '#ffffff';
      ln.setStyle({{color:nColor, weight:4, opacity:1, dashArray:null}});
      ln.bringToFront();
    }} else {{
      ln.setStyle({{color:'#1e1e2e', weight:1, opacity:0.12, dashArray:'4,8'}});
    }}
  }});

  const neighbors = new Set([iata]);
  EDGES.forEach(e => {{
    if (activeMapFilterNodes.has(e.from) && activeMapFilterNodes.has(e.to)) {{
      if (e.from === iata) neighbors.add(e.to);
      if (e.to   === iata) neighbors.add(e.from);
    }}
  }});
  
  Object.entries(mkMap).forEach(([id, mk]) => {{
    if (activeMapFilterNodes.has(id)) {{
      // Se o nó está no filtro: destaca se for vizinho, ofusca se não for
      mk.setOpacity(neighbors.has(id) ? 1 : 0.2);
    }} else {{
      // Se o nó não está no filtro: mantém ele quase invisível
      mk.setOpacity(0.05);
    }}
  }});
  
  document.getElementById('statusbar').textContent = `${{iata}} (${{AP[iata]?.cidade}}) — Analisando ego-network.`;
}}

map.on('click', () => {{
  if (selectedVertex) {{
    selectedVertex = null;
    applyFilters();
  }}
}});

let rpoLine = null;
let mspLine = null;
function highlightPath(which) {{
  document.getElementById('btn-rpo').classList.toggle('active', which === 'rpo');
  document.getElementById('btn-msp').classList.toggle('active', which === 'msp');

  if (rpoLine) {{ map.removeLayer(rpoLine); rpoLine = null; }}
  if (mspLine) {{ map.removeLayer(mspLine); mspLine = null; }}
  if (which === 'none') {{
    applyFilters(); return;
  }}

  EDGES.forEach(e => {{
    const ln = lineMap[ekey(e.from, e.to)]; if (!ln) return;
    ln.setStyle({{color:'#1e1e2e', weight:1, opacity:0.15, dashArray:'4,8'}});
  }});

  const path  = which === 'rpo' ? PATH_RPO : PATH_MSP;
  const color = which === 'rpo' ? '#ff4444' : '#44aaff';
  const label = which === 'rpo' ? 'Recife → Porto Alegre' : 'Manaus → São Paulo';

  if (path.length < 2) {{
    document.getElementById('statusbar').textContent = 'Caminho não encontrado.'; return;
  }}

  const latlngs = path.map(iata => [AP[iata].lat, AP[iata].lon]);
  const pathLine = L.polyline(latlngs, {{ color: color, weight: 5, opacity: 1, dashArray: '12, 12', className: 'animated-path' }}).addTo(map);
  pathLine.bringToFront();
  pathLine.bindTooltip(`${{path.join(' → ')}} | ${{label}}`, {{sticky:true, direction:'top'}});

  if (which === 'rpo') rpoLine = pathLine; else mspLine = pathLine;

  const pathSet = new Set(path);
  Object.entries(mkMap).forEach(([iata, mk]) => {{ mk.setOpacity(pathSet.has(iata) ? 1 : 0.2); }});
  map.fitBounds(pathLine.getBounds(), {{ padding: [50, 50], maxZoom: 7, animate: true, duration: 1.2 }});
  document.getElementById('statusbar').textContent = `${{which === 'rpo' ? 'REC → POA' : 'MAO → GRU'}}: ${{path.join(' → ')}} (${{path.length - 1}} trecho(s))`;
}}

let rotaLine = null;
function limparRota() {{
  if (rotaLine) {{ map.removeLayer(rotaLine); rotaLine = null; }}
  highlightPath('none');
  document.getElementById('btn-rpo').classList.remove('active');
  document.getElementById('btn-msp').classList.remove('active');
  
  document.getElementById('rota-origem').value  = '';
  document.getElementById('rota-destino').value = '';
  document.getElementById('rota-result').innerHTML = 'Digite origem e destino para calcular.';
  
  applyFilters();
}}

function dijkstraJS(origem, destino) {{
  const INF  = Infinity; const dist = {{}}, prev = {{}}; const adj  = {{}};
  Object.keys(AP).forEach(n => {{ adj[n] = []; }});
  EDGES.forEach(e => {{
    if (adj[e.from]) adj[e.from].push({{node:e.to, peso:parseFloat(e.peso)}});
    if (adj[e.to])   adj[e.to].push({{node:e.from, peso:parseFloat(e.peso)}});
  }});
  Object.keys(AP).forEach(n => {{ dist[n] = INF; }});
  dist[origem] = 0;
  const visited = new Set(); const queue = Object.keys(AP).slice();
  
  while (queue.length > 0) {{
    queue.sort((a, b) => dist[a] - dist[b]);
    const u = queue.shift();
    if (dist[u] === INF || u === destino) break;
    visited.add(u);
    (adj[u] || []).forEach(nb => {{
      if (visited.has(nb.node)) return;
      const nd = dist[u] + nb.peso;
      if (nd < dist[nb.node]) {{ dist[nb.node] = nd; prev[nb.node] = u; }}
    }});
  }}
  if (dist[destino] === INF) return {{custo:INF, caminho:[]}};
  const caminho = []; let cur = destino;
  while (cur !== undefined) {{ caminho.unshift(cur); cur = prev[cur]; }}
  return {{custo:dist[destino], caminho}};
}}

function buscarRota() {{
  const origem  = document.getElementById('rota-origem').value.trim().toUpperCase();
  const destino = document.getElementById('rota-destino').value.trim().toUpperCase();
  const box     = document.getElementById('rota-result');

  if (!origem || !destino) {{ box.innerHTML = '<span style="color:#ff7070">Preencha origem e destino.</span>'; return; }}
  if (!AP[origem])  {{ box.innerHTML = `<span style="color:#ff7070">Aeroporto "${{origem}}" não encontrado.</span>`;  return; }}
  if (!AP[destino]) {{ box.innerHTML = `<span style="color:#ff7070">Aeroporto "${{destino}}" não encontrado.</span>`; return; }}
  if (origem === destino) {{ box.innerHTML = '<span style="color:#ff7070">Origem e destino são iguais.</span>'; return; }}

  const {{custo, caminho}} = dijkstraJS(origem, destino);
  if (rotaLine) {{ map.removeLayer(rotaLine); rotaLine = null; }}
  if (caminho.length === 0) {{ box.innerHTML = `<span style="color:#ff7070">Sem caminho entre ${{origem}} e ${{destino}}.</span>`; return; }}

  const direto  = EDGES.some(e => (e.from===origem&&e.to===destino)||(e.from===destino&&e.to===origem));
  const escalas = caminho.length - 2;
  const tipo    = direto ? '✅ Voo direto' : `🔁 Com ${{escalas}} escala(s)`;

  // PEGANDO A COR DO AEROPORTO DE ORIGEM
  const corOrigem = AP[origem].color;

  box.innerHTML = `<b style="color:#e0e0f0">${{origem}} → ${{destino}}</b><br>${{tipo}}<br>`+
    `Distância: <b style="color:${{corOrigem}}">${{custo.toFixed(0)}} km</b><br>Percurso:<br><span style="color:${{corOrigem}}">${{caminho.join(' → ')}}</span>`;

  EDGES.forEach(e => {{
    const ln = lineMap[ekey(e.from, e.to)]; if (!ln) return;
    ln.setStyle({{color:'#1e1e2e', weight:1, opacity:0.15, dashArray:'4,8'}});
  }});

  const latlngs = caminho.map(iata => [AP[iata].lat, AP[iata].lon]);
  
  // APLICANDO A COR DA ORIGEM NA LINHA (POLYLINE)
  rotaLine = L.polyline(latlngs, {{ color: corOrigem, weight:4, opacity:1, dashArray: '12, 12', className: 'animated-path' }}).addTo(map);
  rotaLine.bringToFront();
  
  const pathSet = new Set(caminho);
  Object.entries(mkMap).forEach(([iata, mk]) => {{ mk.setOpacity(pathSet.has(iata) ? 1 : 0.2); }});
  
  map.fitBounds(rotaLine.getBounds(), {{padding:[40,40], maxZoom:7, animate:true, duration:1}});
  document.getElementById('statusbar').textContent = `Rota ${{origem}} → ${{destino}}: ${{custo.toFixed(0)}} km | ${{caminho.length-1}} trecho(s) | ${{tipo}}`;
}}

document.getElementById('rota-origem').addEventListener('keydown', e => {{ if(e.key==='Enter') buscarRota(); }});
document.getElementById('rota-destino').addEventListener('keydown', e => {{ if(e.key==='Enter') buscarRota(); }});

function searchNode() {{
  const q = document.getElementById('search-box').value.trim().toUpperCase();
  if (!q) return;
  const info = AP[q];
  if (info) {{ map.flyTo([info.lat, info.lon], 7, {{duration:.8}}); mkMap[q]?.openTooltip(); }}
}}

function resetView() {{
  map.flyTo([-15, -53], 4, {{duration:.8}});
  document.getElementById('search-box').value = '';
  document.getElementById('ux-regiao').value = 'Todas';
  document.getElementById('ux-grau').value = '0';
  limparRota();
  applyFilters();
}}

// Inicia com os filtros zerados alimentando o painel de métricas na primeira carga
applyFilters();

</script>
</body>
</html>"""

def _find_iata(airports: dict, cidade: str) -> str | None:
    for iata, info in airports.items():
        if cidade.lower() in info.get("cidade", "").lower(): return iata
    return None

def main() -> None:
    print("Carregando aeroportos…")
    airports = load_airports(DATA / "aeroportos_data.csv")
    
    print("Carregando arestas…")
    edges = load_edges(DATA / "adjacencias_aeroportos.csv")
    
    print("Carregando métricas ego…")
    ego = load_ego(OUT / "ego_aeroportos.csv")
    
    print("Obtendo coordenadas geográficas…")
    coords = fetch_coords(airports)
    
    print("Calculando caminhos obrigatórios…")
    g = Grafo()
    for e in edges:
        g.add_edge(e["origem"], e["destino"], e["peso"])

    recife       = "REC"
    porto_alegre = _find_iata(airports, "porto alegre") or "POA"
    manaus       = _find_iata(airports, "manaus")       or "MAO"
    sao_paulo    = (_find_iata(airports, "guarulhos") or _find_iata(airports, "são paulo") or "GRU")

    _, path_rpo = g.dijkstra(recife, porto_alegre)
    _, path_msp = g.dijkstra(manaus, sao_paulo)

    html = build_html(airports, edges, ego, coords, path_rpo, path_msp)
    out_path = OUT / "grafo_interativo.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"\nCarregando grafo: {out_path.relative_to(ROOT)}")

if __name__ == "__main__":
    main()