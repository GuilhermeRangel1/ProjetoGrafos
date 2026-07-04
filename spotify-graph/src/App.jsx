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
        background: 'rgba(255, 249, 235, 0.92)',
        border: '1px solid rgba(128, 101, 67, 0.18)',
        color: '#6e6a53',
        fontFamily: "'Nunito', 'Inter', sans-serif",
        fontSize: '0.7rem',
        padding: '8px 15px',
        borderRadius: 999,
        cursor: 'pointer',
        transition: 'all 0.18s',
        boxShadow: '0 12px 28px rgba(85, 74, 50, 0.16)',
      }}
      onMouseEnter={e => { e.target.style.borderColor = '#8cbf99'; e.target.style.color = '#2f5942' }}
      onMouseLeave={e => { e.target.style.borderColor = 'rgba(128, 101, 67, 0.18)'; e.target.style.color = '#6e6a53' }}
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
      accent: '#5c9f79',
    },
    {
      id: 'spotify',
      icon: '🎵',
      title: 'Grafo Spotify',
      desc: 'Grafo interativo de artistas e gêneros musicais com geração de playlists via BFS e DFS.',
      accent: '#4f8fb8',
    },
  ]

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      background: 'linear-gradient(180deg, #f7edcf 0%, #cfe3c2 54%, #a8cfbf 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "'Nunito', 'Inter', sans-serif",
      gap: 48,
      color: '#354733',
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontFamily: "'Nunito', 'Inter', sans-serif",
          fontWeight: 900,
          fontSize: '2.35rem',
          color: '#2f5942',
          marginBottom: 8,
        }}>
          DataGraph
        </div>
        <div style={{ color: '#6e6a53', fontSize: '0.75rem', letterSpacing: 1.4, fontWeight: 800 }}>
          SELECIONE UMA VISUALIZAÇÃO
        </div>
      </div>

      <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap', justifyContent: 'center' }}>
        {cards.map(card => (
          <button
            key={card.id}
            onClick={() => onSelect(card.id)}
            style={{
              background: 'rgba(255, 249, 235, 0.82)',
              border: `1px solid rgba(128, 101, 67, 0.16)`,
              borderRadius: 18,
              padding: '36px 40px',
              width: 260,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s',
              color: '#354733',
              boxShadow: '0 18px 40px rgba(72, 92, 61, 0.16)',
              backdropFilter: 'blur(10px)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = card.accent
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.boxShadow = `0 22px 46px ${card.accent}35`
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = 'rgba(128, 101, 67, 0.16)'
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = '0 18px 40px rgba(72, 92, 61, 0.16)'
            }}
          >
            <div style={{ fontSize: '2.2rem', marginBottom: 16 }}>{card.icon}</div>
            <div style={{
              fontFamily: "'Nunito', 'Inter', sans-serif",
              fontWeight: 900,
              fontSize: '1rem',
              color: card.accent,
              marginBottom: 10,
            }}>
              {card.title}
            </div>
            <div style={{ fontSize: '0.76rem', color: '#6e6a53', lineHeight: 1.65 }}>
              {card.desc}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

function SpotifyApp({ onBack }) {
  const [selectedNode, setSelectedNode] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [trackSearchQuery, setTrackSearchQuery] = useState('')
  const [showLabels, setShowLabels] = useState(false)
  const [showCharts, setShowCharts] = useState(false)

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
  } = useGraphData({ trackSearchQuery })

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
              Gráficos
            </button>
            <div className="bg-[#12121c]/80 backdrop-blur border border-slate-700/50 rounded-lg px-3 py-2 flex gap-4 text-xs text-slate-400 pointer-events-none">
              <span className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 rounded-full bg-slate-300 inline-block" />
                Nó de gênero
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-500 inline-block" />
                Nó de artista
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
