import { useState, useRef, useCallback } from 'react'
import { useGraphData } from './hooks/useGraphData'
import GraphView from './components/GraphView'
import Sidebar from './components/Sidebar'
import Controls from './components/Controls'
import LoadingScreen from './components/LoadingScreen'
import ChartsPanel from './components/ChartsPanel'

const TAB_H = 44

const tabBarStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  height: TAB_H,
  zIndex: 9999,
  display: 'flex',
  alignItems: 'center',
  background: '#0d0d14',
  borderBottom: '1px solid #252535',
  padding: '0 16px',
  gap: 8,
  fontFamily: "'Space Mono', monospace",
}

const logoStyle = {
  fontFamily: "'Syne', sans-serif",
  fontWeight: 800,
  fontSize: '0.85rem',
  background: 'linear-gradient(90deg,#6c63ff,#00c2a8)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  marginRight: 16,
  letterSpacing: 1,
}

function TabBtn({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? '#6c63ff' : '#13131f',
        border: `1px solid ${active ? '#6c63ff' : '#252535'}`,
        color: active ? '#fff' : '#777799',
        fontFamily: "'Space Mono', monospace",
        fontSize: '0.72rem',
        padding: '4px 14px',
        borderRadius: 4,
        cursor: 'pointer',
        fontWeight: active ? 'bold' : 'normal',
        transition: 'all 0.15s',
      }}
    >
      {label}
    </button>
  )
}

function SpotifyApp() {
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
    if (graphRef.current) {
      graphRef.current.zoomToFit(600, 60)
    }
    setSelectedNode(null)
  }, [])

  const isDone = loadingStatus === 'done'
  const isError = loadingStatus === 'error'
  const isLoading = loadingStatus === 'loading' || loadingStatus === 'idle'

  return (
    <div
      style={{ position: 'absolute', inset: 0, top: TAB_H, overflow: 'hidden', background: '#0a0a0f' }}
    >
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

          {showCharts && (
            <ChartsPanel onClose={() => setShowCharts(false)} />
          )}
        </>
      )}
    </div>
  )
}

export default function App() {
  const [activeTab, setActiveTab] = useState('spotify')

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0d0d14', overflow: 'hidden' }}>
      {/* Tab bar */}
      <div style={tabBarStyle}>
        <span style={logoStyle}>ProjetoGrafos</span>
        <TabBtn
          label="✈ Aeroportos"
          active={activeTab === 'airports'}
          onClick={() => setActiveTab('airports')}
        />
        <TabBtn
          label="🎵 Spotify"
          active={activeTab === 'spotify'}
          onClick={() => setActiveTab('spotify')}
        />
      </div>

      {/* Airport iframe — always mounted to avoid losing map state on tab switch */}
      <iframe
        src="/grafo_interativo.html"
        style={{
          position: 'absolute',
          top: TAB_H,
          left: 0,
          width: '100%',
          height: `calc(100% - ${TAB_H}px)`,
          border: 'none',
          visibility: activeTab === 'airports' ? 'visible' : 'hidden',
          pointerEvents: activeTab === 'airports' ? 'auto' : 'none',
        }}
        title="Aeroportos do Brasil"
      />

      {/* Spotify app — always mounted to avoid reloading graph data on tab switch */}
      <div
        style={{
          visibility: activeTab === 'spotify' ? 'visible' : 'hidden',
          pointerEvents: activeTab === 'spotify' ? 'auto' : 'none',
        }}
      >
        <SpotifyApp />
      </div>
    </div>
  )
}
