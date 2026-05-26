import { useState, useRef, useCallback } from 'react'
import { useGraphData } from './hooks/useGraphData'
import GraphView from './components/GraphView'
import Sidebar from './components/Sidebar'
import Controls from './components/Controls'
import LoadingScreen from './components/LoadingScreen'

export default function App() {
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
  const [showLabels, setShowLabels] = useState(false)

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
    <div className="relative w-screen h-screen overflow-hidden bg-[#0a0a0f]">
      {/* Loading overlay */}
      {(isLoading || isError) && (
        <LoadingScreen progress={loadingProgress} status={loadingStatus} error={error} />
      )}

      {/* Graph canvas — always mounted so ref is stable */}
      {isDone && (
        <>
          <GraphView
            graphData={graphData}
            genreColorMap={genreColorMap}
            selectedNode={selectedNode}
            setSelectedNode={setSelectedNode}
            searchQuery={searchQuery}
            showLabels={showLabels}
            graphRef={graphRef}
          />

          {/* Left controls panel */}
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
            showLabels={showLabels}
            setShowLabels={setShowLabels}
            onResetView={handleResetView}
            nodeCount={graphData.nodes.length}
            linkCount={graphData.links.length}
          />

          {/* Right sidebar */}
          {selectedNode && (
            <Sidebar
              node={selectedNode}
              genreColorMap={genreColorMap}
              onClose={() => setSelectedNode(null)}
            />
          )}

          {/* Top-right mini legend */}
          <div className="absolute top-4 right-4 bg-[#12121c]/80 backdrop-blur border border-slate-700/50 rounded-lg px-3 py-2 flex gap-4 text-xs text-slate-400 pointer-events-none z-10">
            <span className="flex items-center gap-1.5">
              <span className="w-3.5 h-3.5 rounded-full bg-slate-300 inline-block" />
              Genre node
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-slate-500 inline-block" />
              Artist node
            </span>
          </div>
        </>
      )}
    </div>
  )
}
