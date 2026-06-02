import { useEffect, useRef, useState, useMemo } from 'react'
import { GENRES, POP_DIST, KPI_STATS, BFS_LAYERS } from '../data/spotifyChartData'

const RADAR_GENRES = ['pop-film', 'k-pop', 'chill', 'forro', 'death-metal', 'acoustic', 'sertanejo']
const RADAR_COLORS = ['#6c63ff', '#FF6B6B', '#4D96FF', '#FFD93D', '#6BCB77', '#a29bfe', '#00c2a8']

// YlOrRd color stops (matches Python matplotlib colormap)
const YL_OR_RD = [
  [255, 255, 212],
  [254, 217, 142],
  [253, 141,  60],
  [227,  26,  28],
  [177,   0,  38],
]

function ylOrRd(t) {
  const n = YL_OR_RD.length - 1
  const i = Math.min(n - 1, Math.floor(t * n))
  const f = t * n - i
  return YL_OR_RD[i].map((v, k) => Math.round(v + f * (YL_OR_RD[i + 1][k] - v)))
}

// Build matrix chart data from fetched heatmap_data.json
function buildCells(tracks, matrix) {
  const n = tracks.length
  const cells = []
  let maxDist = 0
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      const v = matrix[i][j]
      if (v > maxDist) maxDist = v
      cells.push({ x: tracks[j], y: tracks[i], v })
    }
  }
  return { cells, maxDist }
}

const C = {
  bg:     '#0d0d14',
  surf:   '#13131f',
  border: '#252535',
  accent: '#6c63ff',
  teal:   '#00c2a8',
  text:   '#e0e0f0',
  muted:  '#777799',
}

const cardTitleStyle = {
  fontFamily: "'Syne', sans-serif",
  fontSize: '0.95rem',
  marginBottom: 8,
  color: '#00c2a8',
  textTransform: 'uppercase',
  letterSpacing: 1,
  textAlign: 'center',
}

export default function ChartsPanel({ onClose }) {
  const barCanvasRef    = useRef(null)
  const distCanvasRef   = useRef(null)
  const radarCanvasRef  = useRef(null)
  const algoCanvasRef   = useRef(null)
  const heatCanvasRef   = useRef(null)
  const bfsCanvasRef    = useRef(null)

  const [selGenres, setSelGenres] = useState(['pop-film', 'k-pop', 'forro'])
  const [hubCount, setHubCount]   = useState(10)
  const [timingData, setTimingData] = useState(null)
  const [heatData, setHeatData]     = useState(null)
  const [fullReport, setFullReport] = useState(null)

  const top15 = useMemo(() => [...GENRES].sort((a, b) => b.avg_pop - a.avg_pop).slice(0, 15), [])
  const topN   = useMemo(() => top15.slice(0, hubCount), [top15, hubCount])

  // ── Fetch heatmap track distances from heatmap_data.json ─────────────────
  useEffect(() => {
    fetch('/heatmap_data.json')
      .then(r => r.json())
      .then(({ tracks, matrix }) => setHeatData(buildCells(tracks, matrix)))
      .catch(() => console.warn('heatmap_data.json not found'))
  }, [])

  // ── Fetch timing data from parte2_report.json ─────────────────────────────
  useEffect(() => {
    fetch('/parte2_report.json')
      .then(r => r.json())
      .then(rep => {
        setFullReport(rep)
        const avg = arr => arr.reduce((s, x) => s + x.tempo_s, 0) / arr.length
        setTimingData([
          { label: 'BFS',              avg: avg(rep.bfs),                          color: '#6c63ff' },
          { label: 'DFS',              avg: avg(rep.dfs),                          color: '#00c2a8' },
          { label: 'Dijkstra',         avg: avg(rep.dijkstra),                     color: '#4D96FF' },
          { label: 'BF (sem ciclo)',   avg: avg(rep.bellman_ford_pesos_negativos), color: '#FF6B6B' },
          { label: 'BF (c/ ciclo)',    avg: avg(rep.bellman_ford_ciclo_negativo),  color: '#FFD93D' },
        ])
      })
      .catch(() => {
        setTimingData([
          { label: 'BFS',            avg: 0.020437, color: '#6c63ff' },
          { label: 'DFS',            avg: 0.076547, color: '#00c2a8' },
          { label: 'Dijkstra',       avg: 0.012470, color: '#4D96FF' },
          { label: 'BF (sem ciclo)', avg: 0.002103, color: '#FF6B6B' },
          { label: 'BF (c/ ciclo)',  avg: 0.000120, color: '#FFD93D' },
        ])
      })
  }, [])

  // ── Dados derivados para o Storytelling ──────────────────────────────────
  const insights = useMemo(() => {
    // BFS (sempre disponível via import)
    const bfsTotalVisited = BFS_LAYERS.nos.reduce((s, n) => s + n, 0)
    const bfsMaxDepth     = BFS_LAYERS.camadas[BFS_LAYERS.camadas.length - 1]
    const peakIdx         = BFS_LAYERS.nos.indexOf(Math.max(...BFS_LAYERS.nos))
    const peakLayer       = BFS_LAYERS.camadas[peakIdx]
    const peakNos         = BFS_LAYERS.nos[peakIdx]
    const bfs4LayerNodes  = BFS_LAYERS.nos.slice(0, 5).reduce((s, n) => s + n, 0)

    // Dataset (fallback para os valores reais conhecidos)
    const totalNos    = fullReport?.dataset?.nos_amostra ?? 1921
    const totalArestas = fullReport?.dataset?.arestas    ?? 57630

    const bfsCovPct = ((bfsTotalVisited / (totalNos - 1)) * 100).toFixed(1)
    const bfs4CovPct = ((bfs4LayerNodes / bfsTotalVisited) * 100).toFixed(0)

    // DFS: média de arestas back por execução
    const dfsRuns = fullReport?.dfs ?? []
    const avgBackEdges = dfsRuns.length > 0
      ? Math.round(dfsRuns.reduce((s, r) => s + r.arestas_back, 0) / dfsRuns.length)
      : 34626
    const backEdgesPct = ((avgBackEdges / totalArestas) * 100).toFixed(1)

    // Dijkstra: média de saltos
    const dijRuns = fullReport?.dijkstra ?? []
    const avgSaltos = dijRuns.length > 0
      ? (dijRuns.reduce((s, r) => s + r.saltos, 0) / dijRuns.length).toFixed(1)
      : '5.0'
    const maxSaltosRun = dijRuns.length > 0
      ? dijRuns.reduce((best, r) => r.saltos > best.saltos ? r : best, dijRuns[0])
      : null

    // BF subgrafo
    const bfNosSubgrafo   = 300
    const bfArestasTotal  = 1147
    const bfArestasNeg    = 1036
    const bfNegPct        = ((bfArestasNeg / bfArestasTotal) * 100).toFixed(1)

    // Algoritmos (timing)
    const slowest = timingData ? [...timingData].sort((a, b) => b.avg - a.avg)[0] : { label: 'DFS',   avg: 0.07655 }
    const fastest = timingData ? [...timingData].sort((a, b) => a.avg - b.avg)[0] : { label: 'BF (c/ ciclo)', avg: 0.00012 }
    const bfsT    = timingData?.find(a => a.label === 'BFS')
    const dfsT    = timingData?.find(a => a.label === 'DFS')
    const dijT    = timingData?.find(a => a.label === 'Dijkstra')
    const dfsBfsRatio = bfsT && dfsT ? (dfsT.avg / bfsT.avg).toFixed(1) : '3.7'

    // Gêneros
    const mostPopular   = [...GENRES].sort((a, b) => b.avg_pop    - a.avg_pop)[0]
    const mostEnergetic = [...GENRES].sort((a, b) => b.avg_energy - a.avg_energy)[0]
    const mostCheerful  = [...GENRES].sort((a, b) => b.avg_valence - a.avg_valence)[0]
    const leastDanceable = [...GENRES].sort((a, b) => a.avg_dance - b.avg_dance)[0]

    // Distribuição de popularidade
    const totalTracks = POP_DIST.reduce((s, n) => s + n, 0)
    const topPct  = ((POP_DIST[4] / totalTracks) * 100).toFixed(1)
    const lowPct  = (((POP_DIST[0] + POP_DIST[1]) / totalTracks) * 100).toFixed(1)

    // Heatmap: par mais próximo e mais distante
    let mostSimilar = null, mostDistant = null
    if (heatData) {
      heatData.cells.forEach(c => {
        if (c.x === c.y) return
        if (!mostSimilar || c.v < mostSimilar.v) mostSimilar = c
        if (!mostDistant  || c.v > mostDistant.v)  mostDistant  = c
      })
    }

    return {
      totalNos, totalArestas, bfsTotalVisited, bfsMaxDepth, peakLayer, peakNos,
      bfsCovPct, bfs4CovPct, bfs4LayerNodes,
      avgBackEdges, backEdgesPct,
      avgSaltos, maxSaltosRun,
      bfNosSubgrafo, bfArestasTotal, bfArestasNeg, bfNegPct,
      slowest, fastest, dfsBfsRatio, dijT,
      mostPopular, mostEnergetic, mostCheerful, leastDanceable,
      totalTracks, topPct, lowPct,
      mostSimilar, mostDistant,
    }
  }, [fullReport, timingData, heatData])

  // ── Bar chart: top genres ─────────────────────────────────────────────────
  useEffect(() => {
    const Chart = window.Chart
    if (!Chart || !barCanvasRef.current) return
    const chart = new Chart(barCanvasRef.current.getContext('2d'), {
      type: 'bar',
      data: {
        labels: topN.map(g => g.genre),
        datasets: [{
          data: topN.map(g => g.avg_pop),
          backgroundColor: topN.map((_, i) => `rgba(108,99,255,${1 - i * 0.055})`),
          borderRadius: 6, borderSkipped: false,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => ` ${c.raw} pop. média` } },
        },
        scales: {
          x: { ticks: { color: C.muted, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { color: C.muted, font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.04)' }, min: 0 },
        },
      },
    })
    return () => chart.destroy()
  }, [topN])

  // ── Bar chart: popularity distribution ───────────────────────────────────
  useEffect(() => {
    const Chart = window.Chart
    if (!Chart || !distCanvasRef.current) return
    const chart = new Chart(distCanvasRef.current.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['0–20', '21–40', '41–60', '61–80', '81–100'],
        datasets: [{
          data: POP_DIST,
          backgroundColor: ['#252535', '#333355', '#6c63ff66', '#6c63ff', '#9d99ff'],
          borderRadius: 6, borderSkipped: false,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => ` ${c.raw.toLocaleString('pt-BR')} músicas` } },
        },
        scales: {
          x: { ticks: { color: C.muted, font: { size: 11 } }, grid: { display: false } },
          y: {
            ticks: { color: C.muted, font: { size: 10 }, callback: v => v.toLocaleString('pt-BR') },
            grid: { color: 'rgba(255,255,255,.04)' },
          },
        },
      },
    })
    return () => chart.destroy()
  }, [])

  // ── Radar chart ───────────────────────────────────────────────────────────
  useEffect(() => {
    const Chart = window.Chart
    if (!Chart || !radarCanvasRef.current) return
    const datasets = selGenres.map(g => {
      const d = GENRES.find(x => x.genre === g)
      const ci = RADAR_GENRES.indexOf(g)
      const color = RADAR_COLORS[ci >= 0 ? ci : 0]
      return {
        label: g,
        data: [d.avg_dance * 100, d.avg_energy * 100, d.avg_valence * 100, Math.min(100, d.avg_tempo / 1.6), d.avg_pop],
        backgroundColor: color + '22', borderColor: color, borderWidth: 2,
        pointBackgroundColor: color, pointRadius: 4,
      }
    })
    const chart = new Chart(radarCanvasRef.current.getContext('2d'), {
      type: 'radar',
      data: { labels: ['Danceability', 'Energia', 'Valência', 'Tempo', 'Popularidade'], datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          r: {
            ticks: { display: false, backdropColor: 'transparent' },
            grid: { color: 'rgba(255,255,255,.08)' },
            pointLabels: { color: C.muted, font: { size: 11 } },
            min: 0, max: 100,
          },
        },
      },
    })
    return () => chart.destroy()
  }, [selGenres])

  // ── Horizontal bar chart: algorithm timing (from fetched JSON) ────────────
  useEffect(() => {
    const Chart = window.Chart
    if (!Chart || !algoCanvasRef.current || !timingData) return
    const chart = new Chart(algoCanvasRef.current.getContext('2d'), {
      type: 'bar',
      data: {
        labels: timingData.map(a => a.label),
        datasets: [{
          data: timingData.map(a => parseFloat((a.avg * 1000).toFixed(4))),
          backgroundColor: timingData.map(a => a.color + 'cc'),
          borderColor:     timingData.map(a => a.color),
          borderWidth: 1, borderRadius: 6, borderSkipped: false,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: { label: c => ` ${c.raw.toFixed(4)} ms` },
          },
        },
        scales: {
          x: {
            ticks: {
              color: C.muted, font: { size: 10 },
              callback: v => `${parseFloat(v.toFixed(4))} ms`,
            },
            grid: { color: 'rgba(255,255,255,.04)' },
          },
          y: {
            ticks: { color: C.text, font: { size: 11 } },
            grid: { display: false },
          },
        },
      },
    })
    return () => chart.destroy()
  }, [timingData])

  // ── Matrix heatmap: track pairwise distances (from heatmap_data.json) ─────
  useEffect(() => {
    const Chart = window.Chart
    if (!Chart || !heatCanvasRef.current || !heatData) return
    const { cells, maxDist } = heatData

    // Derive ordered label lists from cells
    const xLabels = [...new Set(cells.map(c => c.x))]
    const yLabels = [...new Set(cells.map(c => c.y))].reverse()
    const n = xLabels.length

    const chart = new Chart(heatCanvasRef.current.getContext('2d'), {
      type: 'matrix',
      data: {
        datasets: [{
          label: 'Distância euclidiana',
          data: cells,
          backgroundColor(ctx) {
            const v = ctx.dataset.data[ctx.dataIndex]?.v ?? 0
            const t = maxDist > 0 ? v / maxDist : 0
            const [r, g, b] = ylOrRd(t)
            return `rgba(${r},${g},${b},0.92)`
          },
          borderColor: 'transparent',
          borderWidth: 1,
          width:  ({ chart }) => (chart.chartArea?.width  ?? 0) / n - 1,
          height: ({ chart }) => (chart.chartArea?.height ?? 0) / n - 1,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: () => '',
              label: ctx => {
                const d = ctx.dataset.data[ctx.dataIndex]
                return ` ${d.y} × ${d.x}: ${d.v.toFixed(4)}`
              },
            },
          },
        },
        scales: {
          x: {
            type: 'category',
            labels: xLabels,
            ticks: {
              color: C.muted, font: { size: 8 },
              maxRotation: 50, minRotation: 40,
            },
            grid: { display: false },
            offset: true,
          },
          y: {
            type: 'category',
            labels: yLabels,
            ticks: { color: C.muted, font: { size: 8 } },
            grid: { display: false },
            offset: true,
          },
        },
      },
    })
    return () => chart.destroy()
  }, [heatData])

  // ── Bar chart: BFS nodes per layer ────────────────────────────────────────
  useEffect(() => {
    const Chart = window.Chart
    if (!Chart || !bfsCanvasRef.current) return
    const chart = new Chart(bfsCanvasRef.current.getContext('2d'), {
      type: 'bar',
      data: {
        labels: BFS_LAYERS.camadas.map(c => `Camada ${c}`),
        datasets: [{
          data: BFS_LAYERS.nos,
          backgroundColor: BFS_LAYERS.nos.map((_, i) => `rgba(0,194,168,${0.35 + i * 0.08})`),
          borderColor: '#00c2a8', borderWidth: 1,
          borderRadius: 6, borderSkipped: false,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => ` ${c.raw} nós` } },
        },
        scales: {
          x: { ticks: { color: C.muted, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { color: C.muted, font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.04)' } },
        },
      },
    })
    return () => chart.destroy()
  }, [])

  const toggleGenre = (g) => {
    setSelGenres(prev =>
      prev.includes(g)
        ? prev.length > 1 ? prev.filter(x => x !== g) : prev
        : prev.length < 4 ? [...prev, g] : prev
    )
  }

  return (
    <div style={{
      position: 'absolute', inset: 0, zIndex: 30,
      background: '#09090f', overflowY: 'auto',
      fontFamily: "'Space Mono', monospace",
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 24px', background: C.surf, borderBottom: `1px solid ${C.border}`,
        position: 'sticky', top: 0, zIndex: 10,
      }}>
        <div>
          <div style={{
            fontFamily: "'Syne', sans-serif", fontSize: '1.1rem',
            background: 'linear-gradient(90deg,#6c63ff,#00c2a8)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            🎵 Spotify Artist-Genre Graph
          </div>
          <div style={{ fontSize: '0.65rem', color: C.muted, marginTop: 2 }}>
            Análise Interativa Parte 2
          </div>
        </div>
        <button onClick={onClose} style={{
          background: C.bg, border: `1px solid ${C.teal}`, color: C.teal,
          fontFamily: 'inherit', fontSize: '0.7rem', padding: '5px 12px',
          borderRadius: 4, cursor: 'pointer', fontWeight: 'bold',
        }}>
          🕸 Ver Grafo
        </button>
      </div>

      {/* Content */}
      <div style={{ padding: '30px 40px', maxWidth: 1600, margin: '0 auto' }}>

        <div style={{ marginBottom: 20, borderBottom: `1px solid ${C.border}`, paddingBottom: 15 }}>
          <h2 style={{ fontFamily: "'Syne', sans-serif", color: C.text, fontSize: '1.4rem' }}>
            Análise Interativa
          </h2>
          <p style={{ color: C.muted, fontSize: '0.8rem', marginTop: 6 }}>
            Visualizações geradas a partir dos dados de áudio do dataset Spotify Tracks (114 gêneros · 114.000 músicas).
          </p>
        </div>

        {/* KPI Grid */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: 1, background: C.border, borderRadius: 12, overflow: 'hidden', marginBottom: 25,
        }}>
          {KPI_STATS.map(kpi => (
            <div key={kpi.label} style={{ background: C.surf, padding: '1.1rem 1rem' }}>
              <div style={{ fontSize: '0.62rem', textTransform: 'uppercase', letterSpacing: '2px', color: C.muted, marginBottom: '0.4rem' }}>{kpi.label}</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: C.text, lineHeight: 1 }}>{kpi.val}</div>
              <div style={{ fontSize: '0.68rem', color: C.muted, marginTop: '0.35rem' }}>{kpi.sub}</div>
            </div>
          ))}
        </div>

        {/* Row 1: genre charts */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 25, marginBottom: 25 }}>

          <ChartCard title="Top Gêneros — Popularidade">
            <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginBottom: 14, flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.63rem', color: C.muted, alignSelf: 'center' }}>Mostrar:</span>
              {[5, 10, 15].map(n => (
                <CtrlBtn key={n} active={hubCount === n} onClick={() => setHubCount(n)}>Top {n}</CtrlBtn>
              ))}
            </div>
            <div style={{ position: 'relative', flex: 1, minHeight: 260 }}>
              <canvas ref={barCanvasRef} />
            </div>
            <p style={{ fontSize: '0.72rem', color: C.muted, marginTop: 12, textAlign: 'center' }}>
              Gêneros ordenados pela popularidade média das faixas.
            </p>
          </ChartCard>

          <ChartCard title="Distribuição de Popularidade">
            <div style={{ position: 'relative', flex: 1, minHeight: 260, marginTop: 42 }}>
              <canvas ref={distCanvasRef} />
            </div>
            <p style={{ fontSize: '0.72rem', color: C.muted, marginTop: 12, textAlign: 'center' }}>
              Distribuição real das 114.000 músicas por faixa de popularidade (0–100).
            </p>
          </ChartCard>

          <ChartCard title="Perfil de Áudio por Gênero">
            <div style={{ display: 'flex', gap: 5, justifyContent: 'center', marginBottom: 12, flexWrap: 'wrap' }}>
              {RADAR_GENRES.map((g, i) => {
                const active = selGenres.includes(g)
                return (
                  <button key={g} onClick={() => toggleGenre(g)} style={{
                    background: active ? RADAR_COLORS[i] + '33' : C.bg,
                    border: `1px solid ${active ? RADAR_COLORS[i] : C.border}`,
                    color: active ? RADAR_COLORS[i] : C.muted,
                    fontFamily: 'inherit', fontSize: '0.62rem',
                    padding: '3px 7px', borderRadius: 4, cursor: 'pointer', transition: 'all 0.15s',
                  }}>
                    {g}
                  </button>
                )
              })}
            </div>
            <div style={{ position: 'relative', flex: 1, minHeight: 220 }}>
              <canvas ref={radarCanvasRef} />
            </div>
            <p style={{ fontSize: '0.72rem', color: C.muted, marginTop: 12, textAlign: 'center' }}>
              Danceability, Energia, Valência, Tempo e Popularidade. Selecione até 4 gêneros.
            </p>
          </ChartCard>
        </div>

        {/* Row 2: algorithm charts */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 25 }}>

          <ChartCard title="Tempo Médio por Algoritmo">
            {!timingData ? (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: C.muted, fontSize: '0.8rem' }}>
                Carregando…
              </div>
            ) : (
              <div style={{ position: 'relative', flex: 1, minHeight: 260, marginTop: 12 }}>
                <canvas ref={algoCanvasRef} />
              </div>
            )}
            <p style={{ fontSize: '0.72rem', color: C.muted, marginTop: 12, textAlign: 'center' }}>
              Média de execuções por algoritmo em ms. Dados do parte2_report.json.
            </p>
          </ChartCard>

          <ChartCard title="Heatmap de Distâncias">
            {!heatData ? (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: C.muted, fontSize: '0.8rem' }}>
                Carregando…
              </div>
            ) : (
              <div style={{ position: 'relative', flex: 1, minHeight: 300, marginTop: 8 }}>
                <canvas ref={heatCanvasRef} />
              </div>
            )}
            <p style={{ fontSize: '0.72rem', color: C.muted, marginTop: 12, textAlign: 'center' }}>
              Distância euclidiana (9 features de áudio) entre as 20 faixas do subgrafo BF — amarelo=próximo, vermelho=distante.
            </p>
          </ChartCard>

          <ChartCard title={`Nós por Camada — BFS`}>
            <div style={{ fontSize: '0.65rem', color: C.muted, textAlign: 'center', marginBottom: 8 }}>
              origem: <span style={{ color: C.teal }}>{BFS_LAYERS.origem}</span>
            </div>
            <div style={{ position: 'relative', flex: 1, minHeight: 260 }}>
              <canvas ref={bfsCanvasRef} />
            </div>
            <p style={{ fontSize: '0.72rem', color: C.muted, marginTop: 12, textAlign: 'center' }}>
              Distribuição dos 1.920 nós visitados por camada de distância em saltos.
            </p>
          </ChartCard>

        </div>

        {/* ── Storytelling Analítico & Insights ── */}
        <div style={{ marginTop: 50, borderBottom: `1px solid ${C.border}`, paddingBottom: 15, marginBottom: 28 }}>
          <h2 style={{ fontFamily: "'Syne', sans-serif", color: C.text, fontSize: '1.4rem' }}>
            📖 Storytelling Analítico & Insights
          </h2>
          <p style={{ color: C.muted, fontSize: '0.8rem', marginTop: 6 }}>
            Discussão crítica e conclusões acionáveis baseadas nos algoritmos de grafos e métricas do dataset Spotify.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 25, marginBottom: 40 }}>

          <InsightCard color="#6c63ff" title="1. Top Gêneros & Distribuição de Popularidade">
            No gráfico de <b>Top Gêneros</b>, <b>{insights.mostPopular.genre}</b> lidera com <b>{insights.mostPopular.avg_pop}</b> de popularidade média — mas a diferença entre o 1º e o 10º colocado é de apenas ~12 pontos, indicando que o topo é surpreendentemente nivelado. A <b>Distribuição de Popularidade</b> explica o porquê: as faixas 0–20, 21–40 e 41–60 concentram quase <b>30% cada</b> das {insights.totalTracks.toLocaleString('pt-BR')} músicas — uma curva quase plana. O tombo é abrupto após 60: apenas <b>{POP_DIST[3].toLocaleString('pt-BR')} músicas</b> (11.9%) chegam a 61–80, e míseros <b>{POP_DIST[4].toLocaleString('pt-BR')} ({insights.topPct}%)</b> alcançam 81–100. Isso revela um <b>limiar viral</b>: cruzar 60 de popularidade não é evolução linear — é um salto qualitativo raro.
          </InsightCard>

          <InsightCard color="#f5a623" title="2. Radar — Perfil de Áudio por Gênero">
            O <b>radar</b> expõe as tensões sonoras do dataset. <b>{insights.mostEnergetic.genre}</b> tem a maior energy (<b>{insights.mostEnergetic.avg_energy}</b>), mas valência de apenas <b>{insights.mostEnergetic.avg_valence}</b> — o gênero mais intenso é também dos menos alegres. Em contrapartida, <b>{insights.mostCheerful.genre}</b> lidera valência (<b>{insights.mostCheerful.avg_valence}</b>) com alta energy (<b>{insights.mostCheerful.avg_energy}</b>) — alta densidade emocional positiva. <b>{insights.mostPopular.genre}</b>, o mais popular, traça um hexágono equilibrado sem pico nem vale em nenhum eixo: seu sucesso vem da <b>ausência de extremos</b>, com apelo universal. Já <b>{insights.leastDanceable.genre}</b> tem o menor danceability (<b>{insights.leastDanceable.avg_dance}</b>) e o radar quase não fecha — perfil de escuta passiva, não de dança.
          </InsightCard>

          <InsightCard color="#ff7070" title="3. Tempo por Algoritmo & Heatmap de Distâncias">
            No gráfico de <b>Tempo Médio</b>, a barra do DFS (<b>{insights.slowest?.label === 'DFS' ? (insights.slowest.avg * 1000).toFixed(1) : '76.5'} ms</b>) é visualmente dominante — <b>{insights.dfsBfsRatio}× acima do BFS</b>. No outro extremo, o <b>BF com ciclo negativo</b> é o mais rápido ({insights.fastest ? (insights.fastest.avg * 1000).toFixed(2) : '0.12'} ms): ao detectar o ciclo artificial (a→b→c→a) ele interrompe a busca imediatamente, sem processar o grafo inteiro. No <b>Heatmap</b>, a diagonal amarela é a única certeza absoluta (distância zero consigo mesmo). O padrão de cores revela clusters sonoros: {heatData && insights.mostSimilar ? <>o par <b>"{insights.mostSimilar.y}"</b> × <b>"{insights.mostSimilar.x}"</b> é o mais próximo (dist. <b>{insights.mostSimilar.v.toFixed(4)}</b>), enquanto <b>"{insights.mostDistant?.y}"</b> × <b>"{insights.mostDistant?.x}"</b> é o mais distante (dist. <b>{insights.mostDistant?.v.toFixed(4)}</b>).</> : <>o padrão de cores vermelho intenso em certas linhas/colunas indica faixas orquestrais isoladas sonicamente do grupo de baladas ao redor.</>}
          </InsightCard>

          <InsightCard color="#00c2a8" title="4. BFS por Camada — A Geometria do Espaço Sonoro">
            O gráfico de <b>Nós por Camada</b> conta a história do grafo em {insights.bfsMaxDepth} passos. A <b>Camada 1 tem exatamente {BFS_LAYERS.nos[1]} nós</b> — confirmando K={BFS_LAYERS.nos[1]} do KNN. A curva acelera para <b>{BFS_LAYERS.nos[3]} nós</b> na camada 3 e atinge o pico de <b>{insights.peakNos} nós na camada {insights.peakLayer}</b>, depois despenca para {BFS_LAYERS.nos[BFS_LAYERS.nos.length - 1]} na camada {insights.bfsMaxDepth}. Esse formato de sino assimétrico é a assinatura de um <b>small-world graph</b>: vizinhanças crescem exponencialmente (1→{BFS_LAYERS.nos[1]}→{BFS_LAYERS.nos[2]}→{BFS_LAYERS.nos[3]}) até saturar o espaço. Em <b>4 camadas já são {insights.bfs4LayerNodes} músicas ({insights.bfs4CovPct}%)</b> alcançadas — as {BFS_LAYERS.nos[BFS_LAYERS.nos.length - 1]} restantes da última camada são as faixas mais periféricas do dataset a partir deste ponto de origem.
          </InsightCard>

        </div>
      </div>
    </div>
  )
}

function ChartCard({ title, children }) {
  return (
    <div style={{
      background: C.surf, border: `1px solid ${C.border}`, borderRadius: 12,
      padding: 25, display: 'flex', flexDirection: 'column', minHeight: 420,
      boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
    }}>
      <h3 style={cardTitleStyle}>{title}</h3>
      {children}
    </div>
  )
}

function InsightCard({ color, title, children }) {
  return (
    <div style={{
      background: C.surf, border: `1px solid ${C.border}`,
      borderTop: `4px solid ${color}`, borderRadius: 12, padding: 25,
      boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
    }}>
      <h3 style={{ color, fontSize: '0.82rem', marginBottom: 14, textTransform: 'uppercase', letterSpacing: 1 }}>
        {title}
      </h3>
      <p style={{ fontSize: '0.8rem', lineHeight: 1.75, color: C.text, textAlign: 'justify' }}>
        {children}
      </p>
    </div>
  )
}

function CtrlBtn({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      background: active ? C.accent : C.bg,
      border: `1px solid ${active ? C.accent : C.border}`,
      color: active ? '#fff' : C.muted,
      fontFamily: 'inherit', fontSize: '0.68rem',
      padding: '4px 10px', borderRadius: 4, cursor: 'pointer', transition: 'all 0.2s',
    }}>
      {children}
    </button>
  )
}
