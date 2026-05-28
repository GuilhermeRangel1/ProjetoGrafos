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
        // Fallback: compute from known JSON values
        setTimingData([
          { label: 'BFS',            avg: 0.020437, color: '#6c63ff' },
          { label: 'DFS',            avg: 0.076547, color: '#00c2a8' },
          { label: 'Dijkstra',       avg: 0.012470, color: '#4D96FF' },
          { label: 'BF (sem ciclo)', avg: 0.002103, color: '#FF6B6B' },
          { label: 'BF (c/ ciclo)',  avg: 0.000120, color: '#FFD93D' },
        ])
      })
  }, [])

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
