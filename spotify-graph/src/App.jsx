import { useState, useRef, useCallback } from 'react'
import { useGraphData } from './hooks/useGraphData'
import GraphView from './components/GraphView'
import Sidebar from './components/Sidebar'
import Controls from './components/Controls'
import LoadingScreen from './components/LoadingScreen'
import ChartsPanel from './components/ChartsPanel'

function BackButton({ onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        zIndex: 9999,
        background: '#13131f',
        border: '1px solid #252535',
        color: '#777799',
        fontFamily: "'Space Mono', monospace",
        fontSize: '0.7rem',
        padding: '6px 14px',
        borderRadius: 4,
        cursor: 'pointer',
        transition: 'all 0.15s',
      }}
      onMouseEnter={e => { e.target.style.borderColor = '#6c63ff'; e.target.style.color = '#fff' }}
      onMouseLeave={e => { e.target.style.borderColor = '#252535'; e.target.style.color = '#777799' }}
    >
      ← Voltar
    </button>
  )
}

function LandingPage({ onSelect }) {
  const cards = [
    {
      id: 'airports',
      icon: '✈',
      title: 'Aeroportos do Brasil',
      desc: 'Rede de aeroportos brasileiros com rotas, algoritmos de caminho e estatísticas regionais.',
      accent: '#6c63ff',
    },
    {
      id: 'spotify',
      icon: '🎵',
      title: 'Grafo Spotify',
      desc: 'Grafo interativo de artistas e gêneros musicais com geração de playlists via BFS e DFS.',
      accent: '#00c2a8',
    },
  ]

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      background: '#0d0d14',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "'Space Mono', monospace",
      gap: 48,
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontFamily: "'Syne', sans-serif",
          fontWeight: 800,
          fontSize: '2rem',
          background: 'linear-gradient(90deg,#6c63ff,#00c2a8)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: 8,
        }}>
          ProjetoGrafos
        </div>
        <div style={{ color: '#777799', fontSize: '0.75rem', letterSpacing: 2 }}>
          SELECIONE UMA VISUALIZAÇÃO
        </div>
      </div>

      <div style={{ display: 'flex', gap: 28 }}>
        {cards.map(card => (
          <button
            key={card.id}
            onClick={() => onSelect(card.id)}
            style={{
              background: '#13131f',
              border: `1px solid #252535`,
              borderRadius: 12,
              padding: '36px 40px',
              width: 260,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s',
              color: '#e0e0f0',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = card.accent
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.boxShadow = `0 8px 32px ${card.accent}22`
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = '#252535'
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            <div style={{ fontSize: '2.2rem', marginBottom: 16 }}>{card.icon}</div>
            <div style={{
              fontFamily: "'Syne', sans-serif",
              fontWeight: 800,
              fontSize: '1rem',
              color: card.accent,
              marginBottom: 10,
            }}>
              {card.title}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#777799', lineHeight: 1.7 }}>
              {card.desc}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

function SpotifyApp({ onBack }) {
  const {
    graphData,
    genreColorMap,
    allGenres,
    loadingProgress,
    loadingStatus,
    error,
    minPopularity,
    setMinPopularity,
    minGenreCount,
    setMinGenreCount,
    activeGenres,
    setActiveGenres,
    maxArtists,
    setMaxArtists,
    showTracks,
    setShowTracks,
  } = useGraphData()

  const [selectedNode, setSelectedNode] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [trackSearchQuery, setTrackSearchQuery] = useState('')
  const [showLabels, setShowLabels] = useState(false)
  const [showCharts, setShowCharts] = useState(false)

  const graphRef = useRef(null)

  const handleResetView = useCallback(() => {
    if (graphRef.current) graphRef.current.zoomToFit(600, 60)
    setSelectedNode(null)
  }, [])

  const isDone = loadingStatus === 'done'
  const isError = loadingStatus === 'error'
  const isLoading = loadingStatus === 'loading' || loadingStatus === 'idle'

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-[#0a0a0f]">
      {(isLoading || isError) && (
        <LoadingScreen progress={loadingProgress} status={loadingStatus} error={error} />
      )}

      {isDone && (
        <>
          <GraphView
            graphData={graphData}
            genreColorMap={genreColorMap}
            selectedNode={selectedNode}
            setSelectedNode={setSelectedNode}
            searchQuery={searchQuery}
            trackSearchQuery={trackSearchQuery}
            showLabels={showLabels}
            graphRef={graphRef}
          />

          <Controls
            allGenres={allGenres}
            genreColorMap={genreColorMap}
            activeGenres={activeGenres}
            setActiveGenres={setActiveGenres}
            minPopularity={minPopularity}
            setMinPopularity={setMinPopularity}
            minGenreCount={minGenreCount}
            setMinGenreCount={setMinGenreCount}
            maxArtists={maxArtists}
            setMaxArtists={setMaxArtists}
            showTracks={showTracks}
            setShowTracks={setShowTracks}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            trackSearchQuery={trackSearchQuery}
            setTrackSearchQuery={setTrackSearchQuery}
            showLabels={showLabels}
            setShowLabels={setShowLabels}
            onResetView={handleResetView}
            nodeCount={graphData.nodes.length}
            linkCount={graphData.links.length}
          />

          {selectedNode && (
            <Sidebar
              node={selectedNode}
              genreColorMap={genreColorMap}
              onClose={() => setSelectedNode(null)}
            />
          )}

          <div className="absolute top-4 right-4 flex flex-col items-end gap-2 z-10">
            <button
              onClick={() => setShowCharts(true)}
              style={{
                background: '#13131f',
                border: '1px solid #00c2a8',
                color: '#00c2a8',
                fontFamily: "'Space Mono', monospace",
                fontSize: '0.7rem',
                padding: '5px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold',
                letterSpacing: '0.5px',
              }}
            >
              📊 Ver Gráficos
            </button>
            <div className="bg-[#12121c]/80 backdrop-blur border border-slate-700/50 rounded-lg px-3 py-2 flex gap-4 text-xs text-slate-400 pointer-events-none">
              <span className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 rounded-full bg-slate-300 inline-block" />
                Genre node
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-500 inline-block" />
                Artist node
              </span>
            </div>
          </div>

          {showCharts && <ChartsPanel onClose={() => setShowCharts(false)} />}
        </>
      )}

      <BackButton onClick={onBack} />
    </div>
  )
}

export default function App() {
  const [view, setView] = useState(null)

  if (view === 'airports') {
    return (
      <>
        <iframe
          src="/grafo_interativo.html"
          style={{ position: 'fixed', inset: 0, width: '100%', height: '100%', border: 'none' }}
          title="Aeroportos do Brasil"
        />
        <BackButton onClick={() => setView(null)} />
      </>
    )
  }

  if (view === 'spotify') {
    return <SpotifyApp onBack={() => setView(null)} />
  }

  return <LandingPage onSelect={setView} />
}
