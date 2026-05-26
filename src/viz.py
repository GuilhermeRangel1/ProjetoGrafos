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

from graphs.algorithms import dijkstra as _dijkstra  # type: ignore

COORDS_FALLBACK: dict[str, tuple[float, float]] = {
    "REC": (-8.1264,  -34.9236),
    "SSA": (-12.9086, -38.3225),
    "FOR": (-3.7763,  -38.5326),
    "NAT": (-5.9114,  -35.2477),
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
                    "grau":          row.get("grau", "?"),
                    "ordem_ego":     row.get("ordem_ego", "?"),
                    "tamanho_ego":   row.get("tamanho_ego", "?"),
                    "densidade_ego": row.get("densidade_ego", "?"),
                }
    return metrics


CACHE_FILE = DATA / "coordenadas.json"


def fetch_coords(airports: dict) -> dict[str, tuple[float, float]]:
    """Retorna {iata: (lat, lon)}. Usa fallback embutido ou cache."""
    cache: dict[str, list] = {}
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)

    updated = False
    for iata in airports:
        if iata in cache:
            continue
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
                print(f"      {iata} ({cidade}): {cache[iata]}")
            else:
                cache[iata] = [-15.0, -50.0]
                print(f"      {iata}: não encontrado, usando centro do Brasil")
            updated = True
            time.sleep(1.1)
        except Exception as ex:
            print(f"      {iata}: erro ({ex}), usando centro do Brasil")
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
        return list(self.adj.keys())

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

def _rcolor(regiao: str) -> str:
    for k, v in REGION_COLORS.items():
        if k.lower() in regiao.lower():
            return v
    return "#aaaaaa"


def build_html(airports, edges, ego, coords, path_rpo, path_msp) -> str:

    def ekey(a, b):
        return "|".join(sorted([a, b]))



    ap_data = {}
    for iata, info in airports.items():
        lat, lon = coords.get(iata, (-15.0, -50.0))
        ap_data[iata] = {
            "cidade":        info["cidade"],
            "regiao":        info["regiao"],
            "lat":           lat,
            "lon":           lon,
            "color":         _rcolor(info["regiao"]),
            "grau":          ego.get(iata, {}).get("grau", "?"),
            "ordem_ego":     ego.get(iata, {}).get("ordem_ego", "?"),
            "tamanho_ego":   ego.get(iata, {}).get("tamanho_ego", "?"),
            "densidade_ego": ego.get(iata, {}).get("densidade_ego", "?"),
        }

    seen: set = set()
    edges_clean = []
    for e in edges:
        k = ekey(e["origem"], e["destino"])
        if k in seen:
            continue
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
.toolbar input{{background:var(--bg);border:1px solid var(--border);color:var(--text);
                font-family:inherit;font-size:.75rem;padding:4px 9px;border-radius:4px;
                width:175px;outline:none;transition:border .2s}}
.toolbar input:focus{{border-color:var(--accent)}}
.toolbar button{{background:var(--bg);border:1px solid var(--border);color:var(--text);
                 font-family:inherit;font-size:.7rem;padding:4px 10px;border-radius:4px;
                 cursor:pointer;transition: all .2s}}
.toolbar button:hover{{background:var(--border)}}
.toolbar button.active{{background:var(--accent);border-color:var(--accent);color:#fff}}
main{{display:flex;flex:1;overflow:hidden; width: 100%;}}

#map-container {{display:flex;flex:1; width:100%;}}
#map{{flex:1}}
#sidebar{{width:228px;background:var(--surf);border-left:1px solid var(--border);
          overflow-y:auto;flex-shrink:0;padding:12px 10px;
          display:flex;flex-direction:column;gap:13px}}
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
    display: none; flex: 1; width: 100%; overflow-y: auto; padding: 40px; background: #09090f;
}}
.charts-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(580px, 1fr)); gap: 35px; max-width: 1600px; margin: 0 auto;
}}
.chart-card {{
    background: var(--surf); border: 1px solid var(--border); border-radius: 12px; padding: 25px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}}
.chart-card h3 {{ font-family: 'Syne', sans-serif; font-size: 1rem; margin-bottom: 14px; color: #00c2a8; text-transform: uppercase; letter-spacing: 1px; }}
.chart-card img {{ max-width: 100%; width: 100%; height: auto; border-radius: 6px; border: 1px solid var(--border); background: #fff;}}
.chart-card p {{ font-size: 0.78rem; color: var(--muted); margin-top: 14px; line-height: 1.6; }}
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
    
    <input id="search-box" class="map-ui" placeholder="Buscar IATA…" oninput="searchNode()"/>
    <button class="map-ui" onclick="resetView()">↺ Reset</button>
    <button id="btn-rpo" class="map-ui" onclick="highlightPath('rpo')">REC → POA</button>
    <button id="btn-msp" class="map-ui" onclick="highlightPath('msp')">MAO → GRU</button>
    <button id="btn-hubs" class="map-ui" onclick="toggleHubs()">★ Subgrafo de Hubs</button>
    <button class="map-ui" onclick="limparRota()">Limpar tudo</button>
  </div>
</header>
<main>
  <div id="map-container">
    <div id="map"></div>
    <div id="sidebar">
      <div>
        <div class="ptitle">Legenda — Regiões</div>
        <div id="legend"></div>
      </div>
      <div>
        <div class="ptitle">Buscar Rota</div>
        <div style="display:flex;flex-direction:column;gap:5px">
          <input id="rota-origem"  class="rota-input" placeholder="Origem (ex: REC)" maxlength="3"/>
          <input id="rota-destino" class="rota-input" placeholder="Destino (ex: POA)" maxlength="3"/>
          <button onclick="buscarRota()" style="margin-top:2px;padding:5px;background:var(--accent);border:none;color:#fff;border-radius:4px;cursor:pointer;font-family:inherit;font-size:.72rem;font-weight:700">🔍 Calcular Rota</button>
          <button onclick="limparRota()" style="padding:4px;background:var(--bg);border:1px solid var(--border);color:var(--muted);border-radius:4px;cursor:pointer;font-family:inherit;font-size:.68rem">✕ Limpar tudo</button>
        </div>
        <div class="ibox" id="rota-result" style="margin-top:6px;min-height:60px">Digite origem e destino para calcular.</div>
      </div>
      <div>
        <div class="ptitle">Aeroporto selecionado</div>
        <div class="ibox" id="node-info">Clique em um aeroporto para ver detalhes.</div>
      </div>
      <div>
        <div class="ptitle">Caminhos obrigatórios</div>
        <div class="pbox">
          <span class="pr">▶ REC → POA</span><br/>
          <span id="txt-rpo" style="color:#888">—</span><br/><br/>
          <span class="pm">▶ MAO → GRU</span><br/>
          <span id="txt-msp" style="color:#888">—</span>
        </div>
      </div>
      <div>
        <div class="ptitle">Estatísticas</div>
        <div class="pbox" id="stats" style="color:#aaa">…</div>
      </div>
    </div>
  </div>

  <div id="charts-container">
    <div class="charts-grid">
      <div style="grid-column: 1 / -1; margin-bottom: 15px; border-bottom: 1px solid var(--border); padding-bottom: 20px;">
         <h2 style="font-family: 'Syne', sans-serif; color: var(--text); font-size: 1.4rem;">Análise Topológica Estrutural</h2>
         <p style="color: var(--muted); font-size: 0.8rem; margin-top: 6px;">Métricas estatísticas consolidadas e distribuições estruturais geradas do grafo.</p>
      </div>

      <div class="chart-card">
          <h3>Ranking de Hubs</h3>
          <img src="vis1_ranking_hubs.png" alt="Ranking de Hubs" onerror="this.parentNode.style.display='none'">
          <p>Aeroportos com maior número de conexões diretas na malha aérea nacional.</p>
      </div>
      <div class="chart-card">
          <h3>Distribuição de Graus</h3>
          <img src="vis2_distribuicao_graus.png" alt="Distribuição de Graus" onerror="this.parentNode.style.display='none'">
          <p>Análise de frequência dos graus dos vértices, mapeando a densidade topológica da malha.</p>
      </div>
      <div class="chart-card">
          <h3>Comparação por Regiões</h3>
          <img src="vis3_comparacao_regioes.png" alt="Comparação Regiões" onerror="this.parentNode.style.display='none'">
          <p>Métricas de conectividade agregadas e normalizadas divididas pelas cinco regiões básicas.</p>
      </div>
      <div class="chart-card">
          <h3>Boxplot de Graus</h3>
          <img src="vis_exp2_boxplot_graus_regiao.png" alt="Boxplot" onerror="this.parentNode.style.display='none'">
          <p>Variabilidade estatística interna e identificação de outliers de tráfego regional.</p>
      </div>
      <div class="chart-card">
          <h3>Grau vs Densidade</h3>
          <img src="vis_exp1_dispersao_grau_densidade.png" alt="Dispersão" onerror="this.parentNode.style.display='none'">
          <p>Relação de correlação entre a conectividade individual do aeroporto e a densidade local.</p>
      </div>
      <div class="chart-card">
          <h3>Subgrafos Regionais</h3>
          <img src="vis_expl1_bolhas_regioes.png" alt="Bolhas Regiões" onerror="this.parentNode.style.display='none'">
          <p>Mapeamento multidimensional relacionando diretamente o tamanho e a ordem dos subgrupos.</p>
      </div>
      <div class="chart-card" style="grid-column: 1 / -1; max-width: 900px; justify-self: center; width: 100%;">
          <h3>Heatmap de Conexões Inter-regionais</h3>
          <img src="vis_expl2_mini_heatmap_regioes.png" alt="Heatmap Regiões" onerror="this.parentNode.style.display='none'">
          <p>Matriz cruzada de intensidade exibindo a densidade de tráfego inter e intra-regional.</p>
      </div>
    </div>
  </div>
</main>
<div id="statusbar">Carregando mapa…</div>

<script>
let showingCharts = false;
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
  }} else {{
      btn.innerHTML = '📊 Ver Gráficos';
      btn.style.borderColor = '#00c2a8';
      btn.style.color = '#00c2a8';
      subtitle.innerHTML = 'Rede de Aeroportos — Grafo Interativo (Etapa 9)';
      subtitle.style.color = 'var(--muted)';
      
      // Ajusta o tamanho da viewport do Leaflet ao retornar
      setTimeout(() => map.invalidateSize(), 50);
  }}
}}

const AP       = {ap_json};
const EDGES    = {edges_json};
const LEGEND   = {legend_json};
const PATH_RPO = {rpo_json};
const PATH_MSP = {msp_json};

document.getElementById('txt-rpo').textContent = PATH_RPO.join(' → ') || '(sem caminho)';
document.getElementById('txt-msp').textContent = PATH_MSP.join(' → ') || '(sem caminho)';
document.getElementById('stats').innerHTML =
  `Aeroportos: <b style="color:#e0e0f0">${{Object.keys(AP).length}}</b><br>`+
  `Conexões: <b style="color:#e0e0f0">${{EDGES.length}}</b><br>`+
  `REC→POA: <b style="color:#ff7070">${{PATH_RPO.length-1}} salto(s)</b><br>`+
  `MAO→GRU: <b style="color:#70b8ff">${{PATH_MSP.length-1}} salto(s)</b>`;

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
  const ln = L.polyline(
    [[a.lat, a.lon], [b.lat, b.lon]],
    {{color:'#3a3a55', weight:1.5, opacity:0.5, dashArray:'5,7'}}
  ).addTo(map);
  ln.bindTooltip(
    `${{e.from}} ↔ ${{e.to}} | ${{e.tipo}} | peso ${{parseFloat(e.peso).toFixed(2)}}`,
    {{sticky:true}}
  );
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
  mk.bindTooltip(
    `<b>${{iata}}</b> — ${{info.cidade}}<br>Região: ${{info.regiao}}<br>Grau: ${{info.grau}}`,
    {{direction:'top'}}
  );
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
    restoreEdges();
    Object.values(mkMap).forEach(mk => mk.setOpacity(1));
    document.getElementById('statusbar').textContent =
      `Grafo pronto — ${{Object.keys(AP).length}} aeroportos, ${{EDGES.length}} conexões.`;
    return;
  }}
  selectedVertex = iata;

  EDGES.forEach(e => {{
    const k  = ekey(e.from, e.to);
    const ln = lineMap[k]; if (!ln) return;
    const connected = (e.from === iata || e.to === iata);
    if (connected) {{
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
    if (e.from === iata) neighbors.add(e.to);
    if (e.to   === iata) neighbors.add(e.from);
  }});
  Object.entries(mkMap).forEach(([id, mk]) => mk.setOpacity(neighbors.has(id) ? 1 : 0.2));

  document.getElementById('statusbar').textContent =
    `${{iata}} (${{AP[iata]?.cidade}}) — ${{neighbors.size - 1}} conexão(ões) destacada(s). Clique novamente para desfazer.`;
}}

function restoreEdges() {{
  EDGES.forEach(e => {{
    const k  = ekey(e.from, e.to);
    const ln = lineMap[k]; if (!ln) return;
    ln.setStyle({{color:'#3a3a55', weight:1.5, opacity:0.5, dashArray:'5,7'}});
  }});
}}

map.on('click', () => {{
  if (selectedVertex) {{
    selectedVertex = null;
    restoreEdges();
    Object.values(mkMap).forEach(mk => mk.setOpacity(1));
    document.getElementById('statusbar').textContent =
      `Grafo pronto — ${{Object.keys(AP).length}} aeroportos, ${{EDGES.length}} conexões.`;
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
    restoreEdges();
    Object.values(mkMap).forEach(mk => mk.setOpacity(1));
    return;
  }}

  EDGES.forEach(e => {{
    const ln = lineMap[ekey(e.from, e.to)]; if (!ln) return;
    ln.setStyle({{color:'#1e1e2e', weight:1, opacity:0.15, dashArray:'4,8'}});
  }});

  const path  = which === 'rpo' ? PATH_RPO : PATH_MSP;
  const color = which === 'rpo' ? '#ff4444' : '#44aaff';
  const label = which === 'rpo' ? 'Recife → Porto Alegre' : 'Manaus → São Paulo';

  if (path.length < 2) {{
    document.getElementById('statusbar').textContent = 'Caminho não encontrado.';
    return;
  }}

  const latlngs = path.map(iata => [AP[iata].lat, AP[iata].lon]);
  const pathLine = L.polyline(latlngs, {{
    color:     color,
    weight:    5,
    opacity:   1,
    dashArray: null,
  }}).addTo(map);
  pathLine.bringToFront();
  pathLine.bindTooltip(
    `${{path.join(' → ')}} | ${{label}}`,
    {{sticky:true, direction:'top'}}
  );

  if (which === 'rpo') rpoLine = pathLine;
  else                 mspLine = pathLine;

  const pathSet = new Set(path);
  Object.entries(mkMap).forEach(([iata, mk]) => {{
    mk.setOpacity(pathSet.has(iata) ? 1 : 0.2);
  }});

  map.fitBounds(pathLine.getBounds(), {{
    padding:  [50, 50],
    maxZoom:  7,
    animate:  true,
    duration: 1.2,
  }});

  document.getElementById('statusbar').textContent =
    `${{which === 'rpo' ? 'REC → POA' : 'MAO → GRU'}}: ${{path.join(' → ')}} (${{path.length - 1}} trecho(s))`;
}}

let rotaLine = null;

function limparRota() {{
  if (rotaLine) {{ map.removeLayer(rotaLine); rotaLine = null; }}

  highlightPath('none');

  document.getElementById('btn-rpo').classList.remove('active');
  document.getElementById('btn-msp').classList.remove('active');

  Object.values(mkMap).forEach(mk => mk.setOpacity(1));

  document.getElementById('rota-origem').value  = '';
  document.getElementById('rota-destino').value = '';
  document.getElementById('rota-result').innerHTML = 'Digite origem e destino para calcular.';
  document.getElementById('statusbar').textContent =
    `Grafo pronto — ${{Object.keys(AP).length}} aeroportos, ${{EDGES.length}} conexões.`;
}}

function dijkstraJS(origem, destino) {{
  const INF  = Infinity;
  const dist = {{}}, prev = {{}};
  const adj  = {{}};
  Object.keys(AP).forEach(n => {{ adj[n] = []; }});
  EDGES.forEach(e => {{
    if (adj[e.from]) adj[e.from].push({{node:e.to,   peso:parseFloat(e.peso)}});
    if (adj[e.to])   adj[e.to].push(  {{node:e.from, peso:parseFloat(e.peso)}});
  }});
  Object.keys(AP).forEach(n => {{ dist[n] = INF; }});
  dist[origem] = 0;
  const visited = new Set();
  const queue   = Object.keys(AP).slice();
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

  if (!origem || !destino) {{
    box.innerHTML = '<span style="color:#ff7070">Preencha origem e destino.</span>'; return;
  }}
  if (!AP[origem])  {{ box.innerHTML = `<span style="color:#ff7070">Aeroporto "${{origem}}" não encontrado.</span>`;  return; }}
  if (!AP[destino]) {{ box.innerHTML = `<span style="color:#ff7070">Aeroporto "${{destino}}" não encontrado.</span>`; return; }}
  if (origem === destino) {{ box.innerHTML = '<span style="color:#ff7070">Origem e destino são iguais.</span>'; return; }}

  const {{custo, caminho}} = dijkstraJS(origem, destino);
  if (rotaLine) {{ map.removeLayer(rotaLine); rotaLine = null; }}

  if (caminho.length === 0) {{
    box.innerHTML = `<span style="color:#ff7070">Sem caminho entre ${{origem}} e ${{destino}}.</span>`; return;
  }}

  const direto  = EDGES.some(e => (e.from===origem&&e.to===destino)||(e.from===destino&&e.to===origem));
  const escalas = caminho.length - 2;
  const tipo    = direto ? '✅ Voo direto' : `🔁 Com ${{escalas}} escala(s)`;

  box.innerHTML =
    `<b style="color:#e0e0f0">${{origem}} → ${{destino}}</b><br>${{tipo}}<br>`+
    `Distância: <b style="color:#00c2a8">${{custo.toFixed(0)}} km</b><br>`+
    `Percurso:<br><span style="color:#f5a623">${{caminho.join(' → ')}}</span>`;

  const latlngs = caminho.map(iata => [AP[iata].lat, AP[iata].lon]);
  rotaLine = L.polyline(latlngs, {{color:'#00c2a8', weight:4, opacity:1, dashArray:null}}).addTo(map);
  rotaLine.bringToFront();
  map.fitBounds(rotaLine.getBounds(), {{padding:[40,40], maxZoom:7, animate:true, duration:1}});

  document.getElementById('statusbar').textContent =
    `Rota ${{origem}} → ${{destino}}: ${{custo.toFixed(0)}} km | ${{caminho.length-1}} trecho(s) | ${{tipo}}`;
}}

document.getElementById('rota-origem') .addEventListener('keydown', e => {{ if(e.key==='Enter') buscarRota(); }});
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
  if (showingHubs) toggleHubs();
  limparRota();
}}

let showingHubs = false;
function toggleHubs() {{
  showingHubs = !showingHubs;
  document.getElementById('btn-hubs').classList.toggle('active', showingHubs);

  if (showingHubs) {{
    const hubNodes = new Set();
    Object.entries(AP).forEach(([iata, info]) => {{
      if ((parseInt(info.grau) || 0) >= 10) {{ hubNodes.add(iata); mkMap[iata]?.setOpacity(1); }}
      else mkMap[iata]?.setOpacity(0.15);
    }});
    EDGES.forEach(e => {{
      const k  = ekey(e.from, e.to);
      const ln = lineMap[k]; if (!ln) return;
      if (hubNodes.has(e.from) && hubNodes.has(e.to)) {{
        ln.setStyle({{color:AP[e.to]?.color||'#e84393', weight:3, opacity:0.9, dashArray:null}});
        ln.bringToFront();
      }} else {{
        ln.setStyle({{opacity:0.05, weight:1, dashArray:'4,8'}});
      }}
    }});
    document.getElementById('statusbar').textContent =
      `Subgrafo de Hubs — ${{hubNodes.size}} aeroportos com grau ≥ 10.`;
  }} else {{
    restoreEdges();
    Object.values(mkMap).forEach(mk => mk.setOpacity(1));
    document.getElementById('statusbar').textContent =
      `Grafo pronto — ${{Object.keys(AP).length}} aeroportos, ${{EDGES.length}} conexões.`;
  }}
}}
</script>
</body>
</html>"""


def _find_iata(airports: dict, cidade: str) -> str | None:
    for iata, info in airports.items():
        if cidade.lower() in info.get("cidade", "").lower():
            return iata
    return None


def main() -> None:
    print("[1/5] Carregando aeroportos…")
    airports = load_airports(DATA / "aeroportos_data.csv")
    print(f"      {len(airports)} aeroportos.")

    print("[2/5] Carregando arestas…")
    edges = load_edges(DATA / "adjacencias_aeroportos.csv")
    print(f"      {len(edges)} arestas.")

    print("[3/5] Carregando métricas ego…")
    ego = load_ego(OUT / "ego_aeroportos.csv")

    print("[4/5] Obtendo coordenadas geográficas…")
    coords = fetch_coords(airports)
    print(f"      {len(coords)} coordenadas prontas.")

    print("[5/5] Calculando caminhos obrigatórios…")
    g = Grafo()
    for e in edges:
        g.add_edge(e["origem"], e["destino"], e["peso"])

    recife       = "REC"
    porto_alegre = _find_iata(airports, "porto alegre") or "POA"
    manaus       = _find_iata(airports, "manaus")       or "MAO"
    sao_paulo    = (
        _find_iata(airports, "guarulhos")
        or _find_iata(airports, "são paulo")
        or "GRU"
    )

    _, path_rpo = g.dijkstra(recife, porto_alegre)
    _, path_msp = g.dijkstra(manaus, sao_paulo)
    print(f"      REC → {porto_alegre}: {' → '.join(path_rpo) or 'sem caminho'}")
    print(f"      {manaus} → {sao_paulo}: {' → '.join(path_msp) or 'sem caminho'}")

    html = build_html(airports, edges, ego, coords, path_rpo, path_msp)
    out_path = OUT / "grafo_interativo.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"\n✅  Gerado: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()