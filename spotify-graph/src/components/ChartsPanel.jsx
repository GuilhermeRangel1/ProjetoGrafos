import { useEffect, useRef, useState, useMemo } from 'react'
import { GENRES, POP_DIST, KPI_STATS, BFS_LAYERS } from '../data/spotifyChartData'
import { displayGenreLabel } from '../utils/genreTranslations'

const RADAR_GENRES = ['pop-film', 'k-pop', 'chill', 'forro', 'death-metal', 'acoustic', 'sertanejo']
const RADAR_COLORS = ['#6c63ff', '#FF6B6B', '#4D96FF', '#FFD93D', '#6BCB77', '#a29bfe', '#00c2a8']

const displayMetricText = (text = '') =>
  text
    .replace(/danceability/gi, 'dançabilidade')
    .replace(/energy/gi, 'energia')
    .replace(/valence/gi, 'valência')
    .replace(/pop\./gi, 'popularidade')

const displayKpiValue = (value = '') => displayGenreLabel(value)

const C = {
  bg:     '#10170f',
  surf:   'rgba(31, 45, 30, 0.9)',
  border: 'rgba(196, 179, 126, 0.35)',
  accent: '#8fbd8c',
  teal:   '#8fbd8c',
  text:   '#f7efcf',
  muted:  '#d9cfad',
}

const cardTitleStyle = {
  fontFamily: "'Syne', sans-serif",
  fontSize: '0.95rem',
  marginBottom: 8,
  color: '#8fbd8c',
  textTransform: 'uppercase',
  letterSpacing: 1,
  textAlign: 'center',
}

export default function ChartsPanel({ onClose }) {
  const barCanvasRef    = useRef(null)
  const distCanvasRef   = useRef(null)
  const radarCanvasRef  = useRef(null)
  const algoCanvasRef   = useRef(null)
  const sonicCanvasRef  = useRef(null)
  const bfsCanvasRef    = useRef(null)

  const [selGenres, setSelGenres] = useState(['pop-film', 'k-pop', 'forro'])
  const [hubCount, setHubCount]   = useState(10)
  const [timingData, setTimingData] = useState(null)
  const [fullReport, setFullReport] = useState(null)

  const top15 = useMemo(() => [...GENRES].sort((a, b) => b.avg_pop - a.avg_pop).slice(0, 15), [])
  const topN   = useMemo(() => top15.slice(0, hubCount), [top15, hubCount])

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

  // ── Dados derivados para a narrativa analítica ───────────────────────────
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

    // Caminhos reais do Dijkstra e Bellman-Ford
    const dijPaths = fullReport?.dijkstra ?? []
    const bonjoviPath = dijPaths.find(p => p.caminho && p.caminho.includes('You Give Love A Bad Name'))
      ?? (dijPaths.length > 0 ? dijPaths[0] : null)
    const bfPaths = fullReport?.bellman_ford_pesos_negativos ?? []
    const bestBfPath = bfPaths.length > 0
      ? bfPaths.reduce((best, r) =>
          typeof r.custo === 'number' && r.custo < (typeof best.custo === 'number' ? best.custo : Infinity) ? r : best,
          bfPaths[0])
      : null
    const bfCycle = fullReport?.bellman_ford_ciclo_negativo?.[0] ?? null

    // BFS stats reais
    const bfsRuns = fullReport?.bfs ?? []
    const minCamadas = bfsRuns.length > 0 ? Math.min(...bfsRuns.map(r => r.camadas)) : 7
    const maxCamadas = bfsRuns.length > 0 ? Math.max(...bfsRuns.map(r => r.camadas)) : 9

    // DFS: percentual de back edges sobre total de arestas
    const dfsBackEdgePct = totalArestas > 0
      ? ((avgBackEdges / totalArestas) * 100).toFixed(1)
      : '60.1'

    // Popularidade: percentual abaixo de 60
    const totalPop = POP_DIST.reduce((s, n) => s + n, 0)
    const obscurePct = (((POP_DIST[0] + POP_DIST[1] + POP_DIST[2]) / totalPop) * 100).toFixed(1)
    const viralPct = ((POP_DIST[4] / totalPop) * 100).toFixed(1)

    // Timing: speedup do BF c/ ciclo vs BFS
    const bfCycleMs = timingData?.find(a => a.label.includes('c/ ciclo'))?.avg ?? 0.00012
    const bfsMs = timingData?.find(a => a.label === 'BFS')?.avg ?? 0.02044
    const cycleSpeedup = Math.round(bfsMs / bfCycleMs)

    return {
      totalNos, totalArestas, bfsTotalVisited, bfsMaxDepth, peakLayer, peakNos,
      bfsCovPct, bfs4CovPct, bfs4LayerNodes,
      avgBackEdges, backEdgesPct, dfsBackEdgePct,
      avgSaltos, maxSaltosRun,
      bfNosSubgrafo, bfArestasTotal, bfArestasNeg, bfNegPct,
      slowest, fastest, dfsBfsRatio, dijT,
      mostPopular, mostEnergetic, mostCheerful, leastDanceable,
      totalTracks, topPct, lowPct,
      bonjoviPath, bestBfPath, bfCycle,
      minCamadas, maxCamadas,
      obscurePct, viralPct,
      cycleSpeedup,
    }
  }, [fullReport, timingData])

  // ── Bar chart: top genres ─────────────────────────────────────────────────
  useEffect(() => {
    const Chart = window.Chart
    if (!Chart || !barCanvasRef.current) return
    const chart = new Chart(barCanvasRef.current.getContext('2d'), {
      type: 'bar',
      data: {
        labels: topN.map(g => displayGenreLabel(g.genre)),
        datasets: [{
          data: topN.map(g => g.avg_pop),
          backgroundColor: topN.map((_, i) => i < 3 ? '#8fbd8cdd' : `rgba(242,217,139,${0.82 - i * 0.025})`),
          borderColor: topN.map((_, i) => i < 3 ? '#8fbd8c' : '#f2d98b'),
          borderWidth: 1,
          borderRadius: 999, borderSkipped: false,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => ` ${c.raw} de popularidade média` } },
        },
        scales: {
          x: { ticks: { color: C.muted, font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.04)' }, min: 0 },
          y: { ticks: { color: C.text, font: { size: 10, weight: '700' } }, grid: { display: false } },
        },
      },
    })
    return () => chart.destroy()
  }, [topN])

  // ── Bar chart: popularity distribution ───────────────────────────────────
  useEffect(() => {
    const Chart = window.Chart
    if (!Chart || !distCanvasRef.current) return
    const ctx = distCanvasRef.current.getContext('2d')
    const gradient = ctx.createLinearGradient(0, 0, 0, 260)
    gradient.addColorStop(0, 'rgba(143,189,140,0.42)')
    gradient.addColorStop(0.55, 'rgba(242,217,139,0.16)')
    gradient.addColorStop(1, 'rgba(16,23,15,0.02)')
    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['0-20', '21-40', '41-60', '61-80', '81-100'],
        datasets: [{
          data: POP_DIST,
          fill: true,
          tension: 0.38,
          backgroundColor: gradient,
          borderColor: '#8fbd8c',
          borderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: ['#f2d98b', '#f2d98b', '#f2d98b', '#c88a9a', '#7fb3d5'],
          pointBorderColor: '#10170f',
          pointBorderWidth: 2,
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
            beginAtZero: true,
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
        label: displayGenreLabel(g),
        data: [d.avg_dance * 100, d.avg_energy * 100, d.avg_valence * 100, Math.min(100, d.avg_tempo / 1.6), d.avg_pop],
        backgroundColor: color + '22', borderColor: color, borderWidth: 2,
        pointBackgroundColor: color, pointRadius: 4,
      }
    })
    const chart = new Chart(radarCanvasRef.current.getContext('2d'), {
      type: 'radar',
      data: { labels: ['Dançabilidade', 'Energia', 'Valência', 'Tempo', 'Popularidade'], datasets },
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

  // ── Bubble chart: genre sonic positioning ─────────────────────────────────
  useEffect(() => {
    const Chart = window.Chart
    if (!Chart || !sonicCanvasRef.current) return
    const palette = ['#8fbd8c', '#f2d98b', '#c88a9a', '#7fb3d5', '#d49a67', '#b9a7e8']
    const chart = new Chart(sonicCanvasRef.current.getContext('2d'), {
      type: 'bubble',
      data: {
        datasets: GENRES.map((genre, index) => {
          const color = palette[index % palette.length]
          return {
            label: displayGenreLabel(genre.genre),
            data: [{
              x: Number((genre.avg_energy * 100).toFixed(1)),
              y: Number((genre.avg_valence * 100).toFixed(1)),
              r: Math.max(5, Math.min(17, 4 + genre.avg_pop / 4)),
              pop: genre.avg_pop,
              dance: genre.avg_dance,
              tempo: genre.avg_tempo,
            }],
            backgroundColor: `${color}99`,
            borderColor: color,
            borderWidth: 1.2,
            hoverBorderWidth: 2,
          }
        }),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: items => items[0]?.dataset?.label ?? '',
              label: ctx => {
                const d = ctx.raw
                return [
                  ` Energia: ${d.x.toFixed(1)}`,
                  ` Valência: ${d.y.toFixed(1)}`,
                  ` Popularidade média: ${d.pop.toFixed(1)}`,
                  ` BPM médio: ${d.tempo.toFixed(1)}`,
                ]
              },
            },
          },
        },
        scales: {
          x: {
            min: 10, max: 100,
            title: { display: true, text: 'Energia média', color: C.muted, font: { size: 11, weight: '700' } },
            ticks: { color: C.muted, font: { size: 10 }, callback: v => `${v}` },
            grid: { color: 'rgba(255,255,255,.05)' },
          },
          y: {
            min: 0, max: 90,
            title: { display: true, text: 'Valência média', color: C.muted, font: { size: 11, weight: '700' } },
            ticks: { color: C.muted, font: { size: 10 }, callback: v => `${v}` },
            grid: { color: 'rgba(255,255,255,.05)' },
          },
        },
      },
    })
    return () => chart.destroy()
  }, [])

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
      background: 'linear-gradient(180deg, #10170f 0%, #182719 48%, #263a2a 100%)',
      overflowY: 'auto',
      fontFamily: "'Nunito', 'Inter', sans-serif",
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 24px', background: 'rgba(31, 45, 30, 0.92)', borderBottom: `1px solid ${C.border}`,
        position: 'sticky', top: 0, zIndex: 10,
      }}>
        <div>
          <div style={{
            fontFamily: "'Syne', sans-serif", fontSize: '1.1rem',
            background: 'linear-gradient(90deg,#efe6c8,#8fbd8c)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            Spotify
          </div>
          <div style={{ fontSize: '0.65rem', color: C.muted, marginTop: 2 }}>
            Análise musical interativa
          </div>
        </div>
        <button onClick={onClose} style={{
          background: 'rgba(16, 23, 15, 0.68)', border: `1px solid rgba(196, 179, 126, 0.38)`, color: '#efe6c8',
          fontFamily: 'inherit', fontSize: '0.7rem', padding: '7px 14px',
          borderRadius: 999, cursor: 'pointer', fontWeight: 800,
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
            Visualizações geradas a partir da base Spotify Tracks (114 gêneros · 114.000 músicas).
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
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: C.text, lineHeight: 1 }}>{displayKpiValue(kpi.val)}</div>
              <div style={{ fontSize: '0.68rem', color: C.muted, marginTop: '0.35rem' }}>{displayMetricText(kpi.sub)}</div>
            </div>
          ))}
        </div>

        {/* Row 1: genre charts */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 25, marginBottom: 25 }}>

          <ChartCard title="Principais Gêneros — Popularidade">
            <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginBottom: 14, flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.63rem', color: C.muted, alignSelf: 'center' }}>Mostrar:</span>
              {[5, 10, 15].map(n => (
                <CtrlBtn key={n} active={hubCount === n} onClick={() => setHubCount(n)}>Ver {n}</CtrlBtn>
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
                    {displayGenreLabel(g)}
                  </button>
                )
              })}
            </div>
            <div style={{ position: 'relative', flex: 1, minHeight: 220 }}>
              <canvas ref={radarCanvasRef} />
            </div>
            <p style={{ fontSize: '0.72rem', color: C.muted, marginTop: 12, textAlign: 'center' }}>
              Dançabilidade, energia, valência, tempo e popularidade. Selecione até 4 gêneros.
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

          <ChartCard title="Mapa Sonoro: Energia × Valência">
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6,
              marginBottom: 8, fontSize: '0.58rem', color: C.muted,
            }}>
              {[
                ['calmo', 'baixa energia'],
                ['intenso', 'alta energia'],
                ['melancólico', 'baixa valência'],
                ['luminoso', 'alta valência'],
              ].map(([label, sub]) => (
                <div key={label} style={{
                  border: `1px solid ${C.border}`, borderRadius: 8,
                  padding: '6px 7px', background: 'rgba(16, 23, 15, 0.42)',
                }}>
                  <b style={{ color: C.text, display: 'block', textTransform: 'uppercase', letterSpacing: 0.7 }}>{label}</b>
                  {sub}
                </div>
              ))}
            </div>
            <div style={{ position: 'relative', flex: 1, minHeight: 300, marginTop: 10 }}>
              <canvas ref={sonicCanvasRef} />
            </div>
            <p style={{ fontSize: '0.72rem', color: C.muted, marginTop: 12, textAlign: 'center' }}>
              Cada bolha representa um gênero: energia no eixo horizontal, valência no vertical e tamanho proporcional à popularidade média.
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

        {/* ── Insights do grafo ── */}
        <section style={{
          marginTop: 52,
          background: 'linear-gradient(135deg, rgba(143,189,140,0.14), rgba(242,217,139,0.08) 48%, rgba(127,179,213,0.10))',
          border: `1px solid ${C.border}`,
          borderRadius: 18,
          padding: 28,
          boxShadow: '0 26px 70px rgba(0,0,0,0.28)',
        }}>
          <div style={{ maxWidth: 1080, marginBottom: 22 }}>
            <div style={{
              color: C.accent, fontSize: '0.68rem', fontWeight: 900,
              letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10,
            }}>
              Leitura interpretativa da rede
            </div>
            <h2 style={{
              fontFamily: "'Syne', sans-serif", color: C.text,
              fontSize: '1.65rem', lineHeight: 1.2, marginBottom: 10,
            }}>
              Insights do Grafo Spotify
            </h2>
            <p style={{ color: C.muted, fontSize: '0.88rem', lineHeight: 1.8, margin: 0 }}>
              O que aparece quando tratamos músicas, artistas e gêneros como uma rede. A leitura combina atributos de áudio, popularidade e caminhos do grafo para explicar
              como a descoberta musical acontece: onde a atenção se concentra, quais gêneros funcionam
              como paisagens sonoras e como os algoritmos constroem pontes entre músicas aparentemente distantes.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
            <InsightMetric label="faixas analisadas" value={insights.totalTracks.toLocaleString('pt-BR')} />
            <InsightMetric label="nós da amostra" value={insights.totalNos.toLocaleString('pt-BR')} />
            <InsightMetric label="conexões" value={insights.totalArestas.toLocaleString('pt-BR')} />
            <InsightMetric label="alcance BFS" value={`${insights.minCamadas}-${insights.maxCamadas} camadas`} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 25, marginBottom: 25 }}>

            <InsightCard color="#8fbd8c" title="1. Mercado de Atenção">
              <p style={{ margin: 0 }}>
                A base revela uma dinâmica de cauda longa: de <b>{insights.totalTracks.toLocaleString('pt-BR')}</b>{' '}
                faixas, só <b>{POP_DIST[4].toLocaleString('pt-BR')} ({insights.viralPct}%)</b> chegam
                ao intervalo 81-100 de popularidade. A maior parte do catálogo fica abaixo da zona de hit,
                mesmo quando pertence a gêneros fortes.
              </p>
              <InsightList items={[
                <>O gênero mais popular é <b>{displayGenreLabel(insights.mostPopular.genre)}</b>, com média <b>{insights.mostPopular.avg_pop}</b>, ainda abaixo de 60.</>,
                <>Isso sugere que popularidade não é distribuída de forma suave: ela se concentra em poucos títulos.</>,
                <>Para recomendação, explorar nichos é essencial para não prender o usuário sempre no repertório mais óbvio.</>,
              ]} />
              <InsightRead color="#8fbd8c">
                Leitura principal: o grafo ajuda a revelar repertório invisível, não apenas confirmar hits.
              </InsightRead>
            </InsightCard>

            <InsightCard color="#f2d98b" title="2. Paisagem Sonora">
              <p style={{ margin: 0 }}>
                Energia e valência contam histórias diferentes. <b>{displayGenreLabel(insights.mostEnergetic.genre)}</b>{' '}
                lidera em energia (<b>{insights.mostEnergetic.avg_energy}</b>), mas não em sensação positiva
                (<b>{insights.mostEnergetic.avg_valence}</b>). Já <b>{displayGenreLabel(insights.mostCheerful.genre)}</b>{' '}
                aparece como o gênero mais alegre, com valência <b>{insights.mostCheerful.avg_valence}</b>.
              </p>
              <InsightList items={[
                <>Uma faixa pode ser intensa sem ser leve, e alegre sem ser necessariamente agressiva.</>,
                <>O mapa sonoro permite escolher músicas por clima, não só por nome de gênero.</>,
                <>Esse tipo de leitura serve para playlists de humor, trilhas, eventos e curadoria editorial.</>,
              ]} />
              <InsightRead color="#f2d98b">
                Leitura principal: gênero é rótulo; energia, valência e ritmo descrevem a experiência.
              </InsightRead>
            </InsightCard>

            <InsightCard color="#c88a9a" title="3. Pontes de Descoberta">
              <p style={{ margin: 0 }}>
                O Dijkstra mostra que músicas distantes no senso comum podem ser conectadas por uma sequência
                curta de similaridades. A média observada é de <b>{insights.avgSaltos} saltos</b>, o que indica
                que o espaço musical é navegável por transições graduais.
              </p>
              <PathTrail
                caminho={insights.bonjoviPath?.caminho ?? 'Two Generals → Song #3 → Whiskey In The Jar → Biermelodie → You Give Love A Bad Name'}
                accent="#c88a9a"
              />
              <InsightList items={[
                <>Cada música no caminho funciona como uma ponte entre textura, energia, timbre e ritmo.</>,
                <>Isso explica por que playlists automáticas podem sair de um estilo para outro sem parecer aleatórias.</>,
                <>A recomendação fica mais convincente quando respeita continuidade sonora, não apenas popularidade.</>,
              ]} />
              <InsightRead color="#c88a9a">
                Leitura principal: boas recomendações são rotas, não saltos bruscos.
              </InsightRead>
            </InsightCard>

            <InsightCard color="#7fb3d5" title="4. Resiliência da Rede">
              <p style={{ margin: 0 }}>
                O BFS indica uma rede de mundo pequeno: os <b>{insights.totalNos.toLocaleString('pt-BR')}</b>{' '}
                nós da amostra são alcançados em <b>{insights.minCamadas}-{insights.maxCamadas}</b> camadas.
                O pico ocorre na camada <b>{insights.peakLayer}</b>, com <b>{insights.peakNos}</b> nós.
              </p>
              <PathTrail
                caminho={insights.bestBfPath?.caminho ?? 'Too Much Heaven → More Than Gravity → Please Don\'t Say You Love Me → SAVE YOURSELF → Oxyrhynchus → Ain\'t No Grave (Sparse) → Go Solo → Thank You for Asking - Acoustic → Hush Little Baby → The Boo Boo Song'}
                accent="#7fb3d5"
              />
              <InsightList items={[
                <>A rede cresce rápido, satura e depois reduz, comportamento típico de mundo pequeno.</>,
                <>Bellman-Ford ajuda a localizar corredores de alta similaridade para playlists mais coerentes.</>,
                <>DFS aponta redundância estrutural: há rotas alternativas quando uma conexão deixa de ser ideal.</>,
              ]} />
              <InsightRead color="#7fb3d5">
                Leitura principal: o grafo transforma descoberta musical em navegação com caminhos alternativos.
              </InsightRead>
            </InsightCard>

          </div>
        </section>

        {/* Synthesis card */}
        <div style={{
          background: C.surf, border: `1px solid ${C.border}`, borderRadius: 12,
          padding: 28, marginBottom: 40, boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
        }}>
          <h3 style={{
            color: C.text, fontSize: '0.85rem', marginBottom: 18,
            textTransform: 'uppercase', letterSpacing: 1,
          }}>
             Síntese Executiva: O que o Grafo Revela
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
            <div>
              <div style={{ color: '#6c63ff', fontSize: '0.68rem', fontWeight: 700, marginBottom: 8, letterSpacing: 1, textTransform: 'uppercase' }}>
                Estrutura do Grafo
              </div>
              <p style={{ fontSize: '0.77rem', color: C.muted, lineHeight: 1.75, margin: 0 }}>
                O KNN com K=30 cria uma rede densa o bastante para conectar repertórios muito diferentes.
                O DFS aponta cerca de {insights.dfsBackEdgePct}% de arestas de retorno entre as{' '}
                {insights.totalArestas.toLocaleString('pt-BR')} conexões, sinal de forte redundância.
                Isso é positivo para descoberta: se um caminho falha, existem rotas alternativas
                para chegar a regiões parecidas do espaço musical.
              </p>
            </div>
            <div>
              <div style={{ color: '#ff7070', fontSize: '0.68rem', fontWeight: 700, marginBottom: 8, letterSpacing: 1, textTransform: 'uppercase' }}>
                Descoberta Central
              </div>
              <p style={{ fontSize: '0.77rem', color: C.muted, lineHeight: 1.75, margin: 0 }}>
                <b style={{ color: C.text }}>Gêneros ajudam a organizar, mas não explicam tudo.</b>{' '}
                O mapa sonoro mostra que energia, valência, dança, tempo e popularidade contam histórias
                diferentes. Por isso, artistas de gêneros distintos podem ficar próximos no grafo quando
                compartilham textura sonora, ritmo ou intensidade emocional.
              </p>
            </div>
            <div>
              <div style={{ color: '#00c2a8', fontSize: '0.68rem', fontWeight: 700, marginBottom: 8, letterSpacing: 1, textTransform: 'uppercase' }}>
                Implicação Prática
              </div>
              <p style={{ fontSize: '0.77rem', color: C.muted, lineHeight: 1.75, margin: 0 }}>
                Um recomendador baseado em{' '}
                <b style={{ color: C.text }}>distância entre atributos de áudio</b> consegue ir além
                da popularidade bruta. Ele pode montar playlists com transições suaves, revelar músicas
                menos conhecidas e preservar coerência sonora. A leitura principal é simples:
                o grafo transforma descoberta musical em problema de navegação.
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

function PathTrail({ caminho, accent = '#6c63ff' }) {
  const songs = caminho.split(' → ')
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, alignItems: 'center', margin: '10px 0' }}>
      {songs.flatMap((song, i) => {
        const pill = (
          <span
            key={`s${i}`}
            title={song}
            style={{
              background: 'rgba(16, 23, 15, 0.68)', border: `1px solid ${accent}55`,
              borderRadius: 4, padding: '2px 7px',
              fontSize: '0.67rem', color: '#efe6c8',
              maxWidth: 145, overflow: 'hidden', textOverflow: 'ellipsis',
              whiteSpace: 'nowrap', display: 'inline-block', flexShrink: 0,
              cursor: 'default',
            }}
          >
            {song}
          </span>
        )
        if (i < songs.length - 1) {
          return [pill, <span key={`a${i}`} style={{ color: accent + '88', fontSize: '0.75rem', flexShrink: 0 }}>→</span>]
        }
        return [pill]
      })}
    </div>
  )
}

function ChartCard({ title, children }) {
  return (
    <div style={{
      background: C.surf, border: `1px solid ${C.border}`, borderRadius: 12,
      padding: 25, display: 'flex', flexDirection: 'column', minHeight: 420,
      boxShadow: '0 22px 52px rgba(0,0,0,0.32)',
    }}>
      <h3 style={cardTitleStyle}>{title}</h3>
      {children}
    </div>
  )
}

function InsightMetric({ label, value }) {
  return (
    <div style={{
      background: 'rgba(16, 23, 15, 0.56)',
      border: `1px solid ${C.border}`,
      borderRadius: 12,
      padding: '14px 16px',
    }}>
      <div style={{
        color: C.muted, fontSize: '0.62rem', letterSpacing: 1.4,
        textTransform: 'uppercase', marginBottom: 7, fontWeight: 800,
      }}>
        {label}
      </div>
      <div style={{
        color: C.text, fontSize: '1.2rem', fontWeight: 900,
        fontFamily: "'Syne', sans-serif", lineHeight: 1.1,
      }}>
        {value}
      </div>
    </div>
  )
}

function InsightList({ items }) {
  return (
    <ul style={{
      margin: '14px 0 0', padding: 0, listStyle: 'none',
      display: 'grid', gap: 8,
    }}>
      {items.map((item, index) => (
        <li key={index} style={{
          display: 'grid', gridTemplateColumns: '10px 1fr', gap: 9,
          alignItems: 'start', color: C.text, fontSize: '0.78rem', lineHeight: 1.65,
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: 999, background: C.accent,
            marginTop: 9, boxShadow: '0 0 0 3px rgba(143,189,140,0.14)',
          }} />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  )
}

function InsightRead({ color, children }) {
  return (
    <div style={{
      marginTop: 16,
      background: `${color}18`,
      border: `1px solid ${color}44`,
      borderRadius: 10,
      padding: '10px 12px',
      color: C.text,
      fontSize: '0.78rem',
      lineHeight: 1.55,
      fontWeight: 800,
    }}>
      {children}
    </div>
  )
}

function InsightCard({ color, title, children }) {
  return (
    <div style={{
      background: C.surf, border: `1px solid ${C.border}`,
      borderTop: `4px solid ${color}`, borderRadius: 12, padding: 25,
      boxShadow: '0 22px 52px rgba(0,0,0,0.32)',
    }}>
      <h3 style={{ color, fontSize: '0.82rem', marginBottom: 14, textTransform: 'uppercase', letterSpacing: 1 }}>
        {title}
      </h3>
      <div style={{ fontSize: '0.8rem', lineHeight: 1.75, color: C.text, textAlign: 'left' }}>
        {children}
      </div>
    </div>
  )
}

function CtrlBtn({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      background: active ? C.accent : 'rgba(16, 23, 15, 0.68)',
      border: `1px solid ${active ? C.accent : C.border}`,
      color: active ? '#10170f' : C.muted,
      fontFamily: 'inherit', fontSize: '0.68rem',
      padding: '5px 11px', borderRadius: 999, cursor: 'pointer', transition: 'all 0.2s',
    }}>
      {children}
    </button>
  )
}
